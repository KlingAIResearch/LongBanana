"""Opaque same-protocol forwarding; credentials and HTTP hops stay local."""
import re


class UpstreamHTTPError(RuntimeError):
    def __init__(self, status, message, error_type="api_error", retry_after=None):
        super().__init__(message)
        self.status = status
        self.error_type = error_type
        self.retry_after = retry_after


def safe_error(response, keys):
    try:
        value = response.json()
        error = value.get("error", value)
        detail = error.get("message", "Upstream rejected request") if isinstance(error, dict) else str(error)
        kind = error.get("type", "api_error") if isinstance(error, dict) else "api_error"
    except (ValueError, AttributeError):
        detail, kind = "Non-JSON upstream error", "api_error"
    for key in filter(None, keys):
        detail = str(detail).replace(key, "[REDACTED]")
    detail = re.sub(r"(?:sk-|AIza)[A-Za-z0-9_.-]+", "[REDACTED]", str(detail))
    retry = response.headers.get("Retry-After")
    if not isinstance(retry, str) or not re.fullmatch(r"[A-Za-z0-9 ,:+-]{1,100}", retry):
        retry = None
    return UpstreamHTTPError(response.status_code, detail[:500], str(kind)[:80], retry)


class NativeReply:
    def __init__(self, response, client, semaphore, streaming):
        self.response, self.client, self.semaphore = response, client, semaphore
        self.streaming, self.closed = streaming, False

    def close(self):
        if not self.closed:
            self.closed = True
            try:
                self.response.close()
            finally:
                try:
                    self.client.close()
                finally:
                    self.semaphore.release()

    def json(self):
        try:
            return self.response.json()
        finally:
            self.close()

    def send(self, handler):
        """No JSON/SSE rewriting, signature decoding, or synthesized events."""
        try:
            if self.streaming:
                content_type = self.response.headers.get("Content-Type", "")
                if "text/event-stream" not in content_type.lower():
                    raise UpstreamHTTPError(502, "Upstream did not return an SSE stream")
                handler.send_response(self.response.status_code)
                handler.send_header("Content-Type", content_type)
                handler.send_header("Cache-Control", "no-cache")
                handler.send_header("Connection", "close")
                handler.end_headers()
                handler.close_connection = True
                raw = self.response.raw
                if hasattr(raw, "read1"):
                    while True:
                        chunk = raw.read1(65536, decode_content=True)
                        if not chunk:
                            break
                        handler.wfile.write(chunk)
                        handler.wfile.flush()
                else:
                    # Old urllib3 fallback: small reads must not buffer a whole turn.
                    for chunk in self.response.iter_content(chunk_size=1):
                        if chunk:
                            handler.wfile.write(chunk)
                            handler.wfile.flush()
            else:
                data = self.response.content
                handler.send_response(self.response.status_code)
                handler.send_header("Content-Type", self.response.headers.get("Content-Type", "application/json"))
                handler.send_header("Content-Length", str(len(data)))
                handler.end_headers()
                handler.wfile.write(data)
        finally:
            self.close()
