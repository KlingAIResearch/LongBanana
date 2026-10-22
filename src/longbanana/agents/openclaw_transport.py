"""Opaque, fixed-provider loopback transport for the unchanged OpenClaw Judge."""
from __future__ import annotations

from contextlib import contextmanager
import copy
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import secrets
import threading
from urllib.parse import unquote, urlsplit

import requests


class Transport:
    def __init__(self, provider, credentials="", timeout=900, buffered_gemini=False):
        self.provider = copy.deepcopy(provider)
        self.credentials = credentials
        self.timeout = timeout
        self.token = secrets.token_urlsafe(32)
        self.lock = threading.Lock()
        self.google_credentials = None
        self.buffered_gemini = buffered_gemini
        self.semaphore = threading.BoundedSemaphore(30)
        self.use_proxy = True

    def endpoint(self, path, body):
        parsed = urlsplit(path)
        suffix = parsed.path.removeprefix("/upstream")
        if not parsed.path.startswith("/upstream/") or parsed.fragment:
            raise ValueError("Unknown local endpoint")
        model = self.provider["models"][0]["id"]
        api = self.provider["api"]
        if api == "google-generative-ai":
            if unquote(suffix) not in (f"/models/{model}:generateContent", f"/models/{model}:streamGenerateContent"):
                raise ValueError("Unexpected model or Gemini operation")
            if parsed.query not in ("", "alt=sse"):
                raise ValueError("Unexpected Gemini query")
        else:
            expected = {"openai-completions": "/chat/completions", "openai-responses": "/responses",
                        "anthropic-messages": "/messages"}.get(api)
            if suffix != expected or parsed.query or json.loads(body).get("model") != model:
                raise ValueError("Unexpected model or protocol endpoint")
        if self.buffered_gemini and api == "google-generative-ai" and suffix.endswith(":streamGenerateContent"):
            # Explicit deployment route, not an error-triggered retry/fallback.
            # Some endpoints expose generateContent only. Preserve the entire payload
            # and every response part/signature; only adapt HTTP/SSE framing.
            return self.provider["baseUrl"].rstrip("/") + suffix.replace(":streamGenerateContent", ":generateContent")
        return self.provider["baseUrl"].rstrip("/") + suffix + ("?" + parsed.query if parsed.query else "")

    def headers(self):
        headers = {"Content-Type": "application/json", **self.provider.get("headers", {})}
        if self.credentials:
            # Refresh before a request, not by replaying a failed paid POST.
            from google.auth.transport.requests import Request
            from google.oauth2 import service_account
            with self.lock:
                if self.google_credentials is None:
                    self.google_credentials = service_account.Credentials.from_service_account_file(
                        self.credentials, scopes=["https://www.googleapis.com/auth/cloud-platform"])
                if not self.google_credentials.valid:
                    self.google_credentials.refresh(Request())
                headers["Authorization"] = "Bearer " + self.google_credentials.token
        else:
            key = self.provider["apiKey"]
            if self.provider["api"] == "google-generative-ai":
                headers["x-goog-api-key"] = key
            elif self.provider["api"] == "anthropic-messages":
                headers.update({"x-api-key": key, "anthropic-version": "2023-06-01"})
            else:
                headers["Authorization"] = "Bearer " + key
        return headers

    def sanitized(self, port):
        result = copy.deepcopy(self.provider)
        result["baseUrl"] = f"http://127.0.0.1:{port}/upstream"
        result["apiKey"] = self.token
        result["headers"] = {"Authorization": "Bearer " + self.token}
        result["request"] = {**result.get("request", {}), "allowPrivateNetwork": True}
        return result


@contextmanager
def serve(transport):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *_):
            pass

        def error(self, status):
            data = json.dumps({"error": {"message": "Judge transport rejected request", "status": status}}).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.close_connection = True
            self.wfile.write(data)

        def do_POST(self):
            supplied = self.headers.get("Authorization", "")
            key = self.headers.get("x-goog-api-key", self.headers.get("x-api-key", ""))
            if not (hmac.compare_digest(supplied, "Bearer " + transport.token) or
                    hmac.compare_digest(key, transport.token)):
                return self.error(401)
            length = self.headers.get("Content-Length", "")
            if not length.isdecimal() or self.headers.get("Transfer-Encoding"):
                return self.error(411)
            if not 0 < int(length) <= 64 * 1024 * 1024:
                return self.error(413)
            body = self.rfile.read(int(length))
            try:
                url = transport.endpoint(self.path, body)
            except (ValueError, KeyError):
                return self.error(400)
            client = requests.Session()
            client.trust_env = False  # no host netrc or accidental proxy/auth
            parsed = urlsplit(url)
            # Honor user-configured bypass rules without inheriting netrc credentials.
            if transport.use_proxy and parsed.hostname not in ("localhost", "127.0.0.1", "::1") and not requests.utils.should_bypass_proxies(url, no_proxy=None):
                import os
                client.proxies = {k: v for k in ("http", "https")
                                  if (v := os.environ.get(k + "_proxy", os.environ.get(k.upper() + "_PROXY")))}
            sent = False
            response = None
            transport.semaphore.acquire()
            try:
                headers = transport.headers()
                # Preserve native Messages feature negotiation, never client auth.
                if transport.provider['api'] == 'anthropic-messages':
                    for name in ('anthropic-version', 'anthropic-beta'):
                        if self.headers.get(name):
                            headers[name] = self.headers[name]
                response = client.post(url, data=body, headers=headers, stream=True,
                                       timeout=transport.timeout, allow_redirects=False)
                if response.status_code >= 300:
                    # Do not expose echoed request bodies/keys in upstream errors.
                    return self.error(response.status_code)
                buffered_sse = (transport.buffered_gemini and transport.provider["api"] == "google-generative-ai"
                                and urlsplit(self.path).path.endswith(":streamGenerateContent"))
                if buffered_sse:
                    data = response.content
                    json.loads(data)  # Reject non-JSON success before sending SSE headers.
                    self.send_response(response.status_code)
                    self.send_header("Content-Type", "text/event-stream")
                    self.send_header("Connection", "close")
                    self.end_headers()
                    self.close_connection = True
                    sent = True
                    for line in data.splitlines():
                        self.wfile.write(b"data: " + line + b"\n")
                    self.wfile.write(b"\n")
                    self.wfile.flush()
                    return
                self.send_response(response.status_code)
                self.send_header("Content-Type", response.headers.get("Content-Type", "application/json"))
                self.send_header("Connection", "close")
                self.end_headers()
                self.close_connection = True
                sent = True
                while True:
                    chunk = response.raw.read1(65536, decode_content=True)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()
            except (requests.RequestException, OSError, ValueError):
                if not sent:
                    self.error(502)
            finally:
                if response is not None:
                    response.close()
                client.close()
                transport.semaphore.release()

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_port
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
