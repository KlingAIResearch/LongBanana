"""Credential-owning loopback image transport; no image or prompt rewriting."""
import hmac
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .native_proxy import UpstreamHTTPError
from .router import Endpoint


def create_image_server(config, token, concurrency=10, timeout=1800, port=0):
    endpoint = Endpoint(config, concurrency, timeout)
    if endpoint.protocol != 'gemini':
        raise ValueError('The image service requires the Gemini protocol')
    if not token:
        raise ValueError('An image service token is required')

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def fail(self, status, message):
            body = json.dumps({'error': {'message': message}}).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            auth = self.headers.get('Authorization', '').removeprefix('Bearer ')
            if not hmac.compare_digest(auth, token):
                return self.fail(401, 'Invalid image service token')
            if self.path != '/generate':
                return self.fail(404, 'Unsupported endpoint')
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 64 * 1024 * 1024:
                    raise ValueError('Invalid request size')
                body = json.loads(self.rfile.read(size))
                if not isinstance(body, dict) or set(body) - {'contents', 'generationConfig'} or not body.get('contents'):
                    raise ValueError('Unsupported image request')
                reply = endpoint.open(body)
                reply.send(self)
            except (BrokenPipeError, ConnectionResetError):
                pass
            except UpstreamHTTPError as exc:
                self.fail(exc.status, str(exc))
            except ValueError:
                self.fail(400, 'Invalid image request')
            except Exception:
                self.fail(502, 'Image upstream request failed')

    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.daemon_threads = True
    return server
