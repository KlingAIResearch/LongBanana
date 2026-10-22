"""Loopback HTTP tests; no external API access or agent runtime required."""
import base64
from contextlib import contextmanager
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import unittest
from unittest.mock import patch

import requests

from longbanana.providers.http_server import create_server
from longbanana.providers.image_service import create_image_server
from longbanana.providers.router import Endpoint, Router
from longbanana.agents.openclaw import ConfiguredTransport
from longbanana.agents.openclaw_transport import serve as serve_openclaw


@contextmanager
def serving(server):
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}'
    finally:
        server.shutdown()
        server.server_close()
        worker.join(3)


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.requests = []
        self.reply = b'{"id":"response-test","output":[]}'
        self.status = 200
        self.kind = 'application/json'
        owner = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass
            def do_POST(self):
                owner.requests.append((self.path, dict(self.headers), self.rfile.read(int(self.headers['Content-Length']))))
                self.send_response(owner.status)
                self.send_header('Content-Type', owner.kind)
                self.send_header('Content-Length', str(len(owner.reply)))
                self.end_headers()
                self.wfile.write(owner.reply)
        self.upstream = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.context = serving(self.upstream)
        self.base = self.context.__enter__()
        self.addCleanup(self.context.__exit__, None, None, None)
        self.env = patch.dict(os.environ, {'TEST_TRANSPORT_KEY': 'upstream-test-key'})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.client = requests.Session()
        self.client.trust_env = False
        self.addCleanup(self.client.close)

    def config(self, protocol='responses'):
        return {'protocol': protocol, 'model': 'test-model', 'base_url': self.base,
                'api_key_env': 'TEST_TRANSPORT_KEY', 'use_proxy': False}

    def test_native_sse_preserved_byte_for_byte(self):
        self.kind = 'text/event-stream'
        self.reply = b'event: response.completed\ndata: {"opaque":"unchanged"}\n\n'
        with serving(create_server(Router(self.config()), 'local-token')) as base:
            result = self.client.post(base + '/v1/responses', headers={'Authorization': 'Bearer local-token'},
                                      json={'model': 'test-model', 'input': 'hello', 'stream': True}, timeout=5)
        self.assertEqual(result.content, self.reply)
        self.assertEqual(self.requests[0][1]['Authorization'], 'Bearer upstream-test-key')
        self.assertNotIn('local-token', self.requests[0][2].decode())

    def test_bad_token_does_not_reach_upstream(self):
        with serving(create_server(Router(self.config()), 'local-token')) as base:
            result = self.client.post(base + '/v1/responses', json={'model': 'test-model'}, timeout=5)
        self.assertEqual(result.status_code, 401)
        self.assertEqual(self.requests, [])

    def test_error_code_preserved_and_key_redacted(self):
        self.status = 429
        self.reply = b'{"error":{"message":"quota for upstream-test-key","type":"rate_limit"}}'
        with serving(create_server(Router(self.config()), 'local-token')) as base:
            result = self.client.post(base + '/v1/responses', headers={'Authorization': 'Bearer local-token'},
                                      json={'model': 'test-model', 'input': 'hello'}, timeout=5)
        self.assertEqual(result.status_code, 429)
        self.assertNotIn('upstream-test-key', result.text)

    def test_gemini_conversion_and_tool_signature_replay(self):
        config = {**self.config('gemini'), 'allow_conversion': True}
        self.reply = json.dumps({'candidates': [{'content': {'parts': [
            {'functionCall': {'name': 'read', 'args': {'path': '/images/a.png'}}, 'thoughtSignature': 'opaque-signature'}]}}]}).encode()
        router = Router(config)
        first = router.run({'model': 'test-model', 'input': 'look', 'tools': [
            {'type': 'function', 'name': 'read', 'parameters': {'type': 'object', 'properties': {'path': {'type': 'string'}}}}]}, 'responses')
        call = next(x for x in first['output'] if x['type'] == 'function_call')
        self.reply = b'{"candidates":[{"content":{"parts":[{"text":"done"}]}}]}'
        router.run({'model': 'test-model', 'previous_response_id': first['id'], 'input': [
            {'type': 'function_call_output', 'call_id': call['call_id'], 'output': 'image-read'}]}, 'responses')
        last = json.loads(self.requests[-1][2])
        parts = [p for c in last['contents'] for p in c['parts']]
        self.assertTrue(any(p.get('thoughtSignature') == 'opaque-signature' for p in parts))

    def test_image_body_is_not_rewritten(self):
        self.reply = b'{"candidates":[{"content":{"parts":[{"inlineData":{"mimeType":"image/png","data":"aGVsbG8="}}]}}]}'
        payload = {'contents': [{'role': 'user', 'parts': [{'text': 'Generate an image.'},
                   {'inlineData': {'mimeType': 'image/png', 'data': base64.b64encode(b'fixture').decode()}}]}],
                   'generationConfig': {'responseModalities': ['TEXT', 'IMAGE']}}
        with serving(create_image_server(self.config('gemini'), 'local-image-token')) as base:
            result = self.client.post(base + '/generate', headers={'Authorization': 'Bearer local-image-token'}, json=payload, timeout=5)
        self.assertEqual(result.content, self.reply)
        self.assertEqual(json.loads(self.requests[-1][2]), payload)
        self.assertEqual(self.requests[-1][0], '/models/test-model:generateContent')

    def test_semaphore_released_after_error(self):
        endpoint = Endpoint(self.config(), concurrency=1)
        self.status = 500
        with self.assertRaises(RuntimeError):
            endpoint.open({'model': 'test-model'})
        self.assertTrue(endpoint.semaphore.acquire(blocking=False))
        endpoint.semaphore.release()

    def test_openclaw_native_messages_preserves_body_and_beta(self):
        transport = ConfiguredTransport(self.config('anthropic'), concurrency=1)
        payload = {'model': 'test-model', 'messages': [{'role': 'assistant', 'content': [
            {'type': 'thinking', 'thinking': 'opaque', 'signature': 'opaque-signature'}]}]}
        with serve_openclaw(transport) as port:
            provider = transport.sanitized(port)
            self.assertNotIn('upstream-test-key', json.dumps(provider))
            result = self.client.post(provider['baseUrl'] + '/messages',
                headers={'Authorization': 'Bearer ' + transport.token, 'anthropic-beta': 'fixture-feature'},
                json=payload, timeout=5)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(json.loads(self.requests[0][2]), payload)
        self.assertEqual(self.requests[0][1]['anthropic-beta'], 'fixture-feature')
        self.assertEqual(self.requests[0][1]['x-api-key'], 'upstream-test-key')

    def test_openclaw_model_rejection_and_error_release(self):
        transport = ConfiguredTransport(self.config(), concurrency=1)
        self.status = 429
        self.reply = b'{"error":"upstream-test-key"}'
        with serve_openclaw(transport) as port:
            url = transport.sanitized(port)['baseUrl'] + '/responses'
            headers = {'Authorization': 'Bearer ' + transport.token}
            wrong = self.client.post(url, headers=headers, json={'model': 'other-model'}, timeout=5)
            self.assertEqual(wrong.status_code, 400)
            self.assertEqual(self.requests, [])
            failed = self.client.post(url, headers=headers, json={'model': 'test-model'}, timeout=5)
        self.assertEqual(failed.status_code, 429)
        self.assertNotIn('upstream-test-key', failed.text)
        self.assertTrue(transport.semaphore.acquire(blocking=False))
        transport.semaphore.release()

    def test_openclaw_buffered_gemini_preserves_signature(self):
        self.reply = json.dumps({'candidates': [{'content': {'parts': [
            {'functionCall': {'name': 'read', 'args': {}}, 'thoughtSignature': 'opaque-signature'}]}}]}).encode()
        transport = ConfiguredTransport(self.config('gemini'), buffered_gemini=True)
        payload = {'contents': [{'role': 'user', 'parts': [{'text': 'look'}]}]}
        with serve_openclaw(transport) as port:
            result = self.client.post(transport.sanitized(port)['baseUrl'] + '/models/test-model:streamGenerateContent?alt=sse',
                headers={'x-goog-api-key': transport.token}, json=payload, timeout=5)
        self.assertEqual(result.content, b'data: ' + self.reply + b'\n\n')
        self.assertEqual(self.requests[0][0], '/models/test-model:generateContent')
        self.assertEqual(json.loads(self.requests[0][2]), payload)


if __name__ == '__main__':
    unittest.main()
