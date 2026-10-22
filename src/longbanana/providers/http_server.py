import hmac
import json
import time
import requests
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from .conversion import events
from .native_proxy import UpstreamHTTPError

def create_server(router, token, port=0):
    if not token:
        raise ValueError("A router token is required")
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def send_json(self, status, value, retry_after=None):
            data = json.dumps(value).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            if retry_after:
                self.send_header("Retry-After", retry_after)
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path == "/health":
                health = getattr(router, "health", None)
                value = health() if health else {"ready": True, "routes": list(router.backends)}
                self.send_json(200 if value.get("ready") else 503, value)
            else:
                self.send_json(404, {"error": {"message": "Not found"}})

        def do_POST(self):
            auth = self.headers.get("Authorization", "").removeprefix("Bearer ")
            auth = self.headers.get("x-api-key", auth)
            if not hmac.compare_digest(auth, token):
                self.send_json(401, {"type": "error", "error": {"type": "authentication_error", "message": "Invalid router token"}})
                return
            path = self.path.split("?", 1)[0]
            if path not in ("/v1/messages", "/v1/responses"):
                self.send_json(404, {"error": {"message": "Unsupported endpoint"}})
                return
            start = time.monotonic()
            proto = "anthropic" if path == "/v1/messages" else "responses"
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 64 * 1024 * 1024:
                    raise ValueError("Invalid request size")
                body = json.loads(self.rfile.read(size))
                if not isinstance(body, dict):
                    raise ValueError("Expected a JSON object")
                forward = getattr(router, "open_native", None)
                native = forward(body, proto, self.headers) if forward else None
                if native is not None:
                    # Native protocols bypass Converter/Shadow and fake SSE.
                    try:
                        native.send(self)
                    except (BrokenPipeError, ConnectionResetError):
                        pass
                    except Exception as exc:
                        if not native.streaming:
                            raise
                        # Headers already sent: terminate the stream, never append
                        # a fake completion or a second HTTP response.
                        self.close_connection = True
                        print(json.dumps({"route": body["model"], "protocol": proto,
                                          "transport": getattr(native, "transport", "native"), "error_type": type(exc).__name__,
                                          "stream_aborted": True}), flush=True)
                        return
                    print(json.dumps({"route": body["model"], "protocol": proto,
                                      "transport": getattr(native, "transport", "native"), "duration_s": round(time.monotonic() - start, 2)}), flush=True)
                    return
                result = router.run(body, proto)
            except Exception as exc:
                status = exc.status if isinstance(exc, UpstreamHTTPError) else (400 if isinstance(exc, (ValueError, KeyError)) else (504 if isinstance(exc, requests.Timeout) else 502))
                message = str(exc) if isinstance(exc, (ValueError, RuntimeError)) else type(exc).__name__
                self.send_json(status, {"type": "error", "error": {"type": exc.error_type if isinstance(exc, UpstreamHTTPError) else ("invalid_request_error" if status == 400 else "api_error"), "message": message}}, exc.retry_after if isinstance(exc, UpstreamHTTPError) else None)
                print(json.dumps({"protocol": proto, "status": status, "error_type": type(exc).__name__, "message": message}), flush=True)
                return
            try:
                if body.get("stream"):
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.end_headers()
                    for index, (event, data) in enumerate(events(result, proto)):
                        if proto == "responses":
                            data["sequence_number"] = index
                        self.wfile.write(("event: " + event + "\ndata: " + json.dumps(data) + "\n\n").encode())
                        self.wfile.flush()
                else:
                    self.send_json(200, result)
            except (BrokenPipeError, ConnectionResetError):
                pass
            print(json.dumps({"route": body["model"], "protocol": proto, "duration_s": round(time.monotonic() - start, 2), "usage": result.get("usage")}), flush=True)
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    return server

