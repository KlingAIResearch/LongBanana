"""Explicit protocol routing; native paths preserve upstream bytes."""
import copy
import os
import threading
from urllib.parse import urlsplit

import requests

from .conversion import Converter, Shadow
from .native_proxy import NativeReply, UpstreamHTTPError, safe_error
from .protocol_helpers import to_chat, to_responses, canonical_response
from .transport_images import compress_responses_images, compress_images

PROTOCOLS = {'responses', 'anthropic', 'gemini', 'chat'}


class Endpoint:
    def __init__(self, config, concurrency=30, timeout=300):
        if type(concurrency) is not int or concurrency < 1 or timeout <= 0:
            raise ValueError('Concurrency and timeout must be positive')
        self.config = copy.deepcopy(config)
        self.protocol = config['protocol']
        if self.protocol not in PROTOCOLS: raise ValueError('Unsupported protocol')
        self.model = config['model']
        if not isinstance(self.model, str) or not self.model.strip() or any(c in self.model for c in '?#'):
            raise ValueError('Invalid model ID')
        self.base = config['base_url'].strip().rstrip('/')
        parsed = urlsplit(self.base)
        if parsed.scheme not in {'https', 'http'} or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError('Expected an HTTP(S) API base URL without credentials or query')
        self.key = os.environ.get(config.get('api_key_env', ''), '')
        self.credentials = None
        self.auth_lock = threading.Lock()
        if config.get('credentials_env'):
            from google.oauth2 import service_account
            self.credentials = service_account.Credentials.from_service_account_file(
                os.environ[config['credentials_env']], scopes=['https://www.googleapis.com/auth/cloud-platform'])
        if not self.key and not self.credentials: raise ValueError('API credentials are not configured')
        self.semaphore = threading.BoundedSemaphore(concurrency)
        self.timeout = timeout

    def url(self):
        suffix = {'responses': '/responses', 'anthropic': '/messages', 'chat': '/chat/completions',
                  'gemini': '/models/' + self.model + ':generateContent'}[self.protocol]
        return self.base + suffix

    def headers(self):
        headers = {'Content-Type': 'application/json'}
        if self.credentials:
            from google.auth.transport.requests import Request
            with self.auth_lock:
                if not self.credentials.valid: self.credentials.refresh(Request())
                headers['Authorization'] = 'Bearer ' + self.credentials.token
        elif self.protocol == 'anthropic':
            headers.update({'x-api-key': self.key, 'anthropic-version': '2023-06-01'})
        elif self.protocol == 'gemini': headers['x-goog-api-key'] = self.key
        else: headers['Authorization'] = 'Bearer ' + self.key
        for name, env_name in self.config.get('headers_env', {}).items():
            headers[name] = os.environ[env_name]
        headers.update(self.config.get('headers', {}))
        return headers

    def open(self, payload, streaming=False, client_headers=None):
        headers = self.headers()
        if self.protocol == 'anthropic' and client_headers:
            for name in ('anthropic-version', 'anthropic-beta'):
                if client_headers.get(name): headers[name] = client_headers[name]
        client = requests.Session()
        client.trust_env = False
        client.proxies = requests.utils.get_environ_proxies(self.url()) if self.config.get('use_proxy', True) else {}
        self.semaphore.acquire()
        response = None
        try:
            response = client.post(self.url(), headers=headers, json=payload,
                                   timeout=(20, self.timeout), stream=streaming, allow_redirects=False)
            if not 200 <= response.status_code < 300:
                error = safe_error(response, [self.key, *headers.values()])
                raise error
            if streaming and 'text/event-stream' not in response.headers.get('Content-Type', '').lower():
                raise UpstreamHTTPError(502, 'Expected an upstream SSE stream')
            return NativeReply(response, client, self.semaphore, streaming)
        except Exception:
            if response is not None: response.close()
            client.close()
            self.semaphore.release()
            raise


def to_anthropic(canonical, model):
    chat = to_chat(canonical, model)
    system, messages = [], []
    for msg in chat['messages']:
        if msg['role'] == 'system':
            system.append(msg['content']); continue
        if msg['role'] == 'tool':
            role = 'user'
            blocks = [{'type': 'tool_result', 'tool_use_id': msg['tool_call_id'], 'content': msg['content']}]
        else:
            role = msg['role']; content = msg.get('content') or []
            if isinstance(content, str): content = [{'type': 'text', 'text': content}]
            blocks = []
            for block in content:
                if block['type'] == 'image_url':
                    header, data = block['image_url']['url'].split(',', 1)
                    blocks.append({'type': 'image', 'source': {'type': 'base64', 'media_type': header[5:].split(';')[0], 'data': data}})
                else: blocks.append(block)
            for call in msg.get('tool_calls', []):
                import json
                blocks.append({'type': 'tool_use', 'id': call['id'], 'name': call['function']['name'], 'input': json.loads(call['function']['arguments'])})
        if messages and messages[-1]['role'] == role: messages[-1]['content'].extend(blocks)
        else: messages.append({'role': role, 'content': blocks})
    result = {'model': model, 'messages': messages, 'max_tokens': chat.get('max_completion_tokens', 16384)}
    if system: result['system'] = '\n'.join(system)
    if chat.get('tools'):
        result['tools'] = [{'name': t['function']['name'], 'description': t['function'].get('description', ''),
                            'input_schema': t['function']['parameters']} for t in chat['tools']]
    choice = chat.get('tool_choice')
    if choice:
        result['tool_choice'] = ({'type': 'tool', 'name': choice['function']['name']} if isinstance(choice, dict)
                                 else {'type': {'required': 'any', 'auto': 'auto', 'none': 'none'}[choice]})
    for name in ('temperature', 'top_p'):
        if name in chat: result[name] = chat[name]
    return result


def anthropic_response(value):
    parts = []
    for block in value.get('content', []):
        if block['type'] == 'text': parts.append({'text': block['text']})
        elif block['type'] == 'tool_use':
            parts.append({'functionCall': {'name': block['name'], 'id': block['id'], 'args': block['input']}})
        elif block['type'] in {'thinking', 'redacted_thinking'}:
            raise ValueError('Thinking-block conversion requires native Messages; use a native route')
    usage = value.get('usage', {})
    return {'candidates': [{'content': {'parts': parts}, 'finishReason': 'MAX_TOKENS' if value.get('stop_reason') == 'max_tokens' else 'STOP'}],
            'usageMetadata': {'promptTokenCount': usage.get('input_tokens', 0), 'candidatesTokenCount': usage.get('output_tokens', 0),
                              'cachedContentTokenCount': usage.get('cache_read_input_tokens', 0)}}


class Router:
    def __init__(self, config, concurrency=30, timeout=300):
        self.endpoint = Endpoint(config, concurrency, timeout)
        self.backends = {config['model']: self.endpoint.protocol}
        self.shadow = Shadow()

    def validate(self, body):
        if not isinstance(body, dict) or body.get('model') != self.endpoint.model:
            raise ValueError('Unknown configured model')

    def open_native(self, body, proto, client_headers=None):
        self.validate(body)
        if self.endpoint.protocol != proto: return None
        payload = copy.deepcopy(body)
        quality = self.endpoint.config.get('image_jpeg_quality')
        if quality is not None:
            if proto != 'responses' or quality != 90: raise ValueError('JPEG transport requires Responses quality 90')
            payload, _ = compress_responses_images(payload, quality)
        return self.endpoint.open(payload, bool(body.get('stream')), client_headers)

    def run(self, body, proto):
        self.validate(body)
        reply = self.open_native({**body, 'stream': False}, proto)
        if reply: return reply.json()
        if not self.endpoint.config.get('allow_conversion', False):
            raise ValueError('Protocol conversion is not enabled for this route')
        converter = Converter(self.endpoint.model, self.shadow)
        canonical = converter.request(body, proto)
        protocol = self.endpoint.protocol
        if protocol == 'gemini': payload = canonical
        elif protocol == 'responses': payload = to_responses(canonical, self.endpoint.model)
        elif protocol == 'chat': payload = to_chat(canonical, self.endpoint.model)
        else: payload = to_anthropic(canonical, self.endpoint.model)
        try:
            value = self.endpoint.open(payload).json()
        except UpstreamHTTPError as exc:
            if exc.status != 413 or protocol != 'gemini' or not self.endpoint.config.get('resize_on_413', False): raise
            for edge, quality in ((1024, 85), (768, 75)):
                resized, stats = compress_images(payload, max_edge=edge, quality=quality)
                if not stats['changed']: raise exc
                try:
                    value = self.endpoint.open(resized).json(); break
                except UpstreamHTTPError as retry:
                    if retry.status != 413 or edge == 768: raise
        if protocol in {'responses', 'chat'}: value = canonical_response(value, protocol == 'responses')
        elif protocol == 'anthropic': value = anthropic_response(value)
        return converter.response(value, body, proto, canonical)
