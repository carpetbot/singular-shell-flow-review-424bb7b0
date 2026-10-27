#!/usr/bin/env python3
"""Singular shell — static server + same-origin gateway proxy.

Why a proxy: api.impossi.build sends NO CORS headers (verified 2026-10-14:
OPTIONS preflight -> 404, no access-control-*). A browser UI therefore cannot
call the gateway directly; it calls /v1/* on this origin and we forward.

The API key stays in the browser (localStorage) and rides in the
Authorization header on every request — the proxy never persists it.

Run:  python3 proxy.py [port]   (default 8730)
Then open http://localhost:8730
"""
import http.server, urllib.request, urllib.error, json, sys, os, re

MAX_VIDEO_BYTES = 100 * 1024 * 1024

class NoMediaRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

GATEWAY = "https://api.impossi.build"
ROOT = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "singular-shell/0.1"}

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def _corsless_copy(self, resp, body):
        self.send_response(resp.status if hasattr(resp, "status") else resp.getcode())
        for k, v in (resp.headers.items() if resp.headers else []):
            if k.lower() in ("content-length", "transfer-encoding", "content-encoding", "connection"):
                continue
            self.send_header(k, v)
        self.send_header("X-Served-By", "singular-shell-proxy")
        self.end_headers()
        self.wfile.write(body)

    def _proxy(self, method):
        path = self.path  # e.g. /v1/chat/completions or /pricing.json
        media = path.startswith('/v1/videos')
        if media and not (path == '/v1/videos' or (method in ('GET', 'HEAD') and re.fullmatch(r'/v1/videos/[A-Za-z0-9_-]{1,160}(?:/content)?', path))):
            self.send_error(404)
            return
        content = media and path.endswith('/content')
        url = GATEWAY + path
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else None
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("User-Agent", "singular-shell/0.1 (+local dev shell)")
        if self.headers.get("Authorization"):
            req.add_header("Authorization", self.headers["Authorization"])
        if body:
            req.add_header("Content-Type", self.headers.get("Content-Type", "application/json"))
        if method == 'POST' and path == '/v1/videos' and self.headers.get('Idempotency-Key'):
            req.add_header('Idempotency-Key', self.headers['Idempotency-Key'])
        want_stream = "text/event-stream" in (self.headers.get("Accept") or "")
        try:
            opener = urllib.request.build_opener(NoMediaRedirect()).open if media else urllib.request.urlopen
            with opener(req, timeout=300) as r:
                ctype = r.headers.get("Content-Type", "")
                if content:
                    self._stream_video(r, method)
                elif want_stream and "event-stream" in ctype:
                    # stream SSE through chunk-by-chunk
                    self.send_response(200)
                    self.send_header("Content-Type", ctype)
                    self.send_header("Cache-Control", "no-cache")
                    self.end_headers()
                    while True:
                        chunk = r.read(1024)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        self.wfile.flush()
                else:
                    self._corsless_copy(r, r.read())
        except urllib.error.HTTPError as e:
            if media:
                # Never buffer or reflect upstream diagnostics/headers (may contain secrets).
                # Closing without draining also bounds untrusted or endless error bodies.
                e.close()
                status = 502 if 300 <= e.code < 400 else e.code
                data = json.dumps({'error_message': 'Video gateway request failed', 'status': status}).encode()
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Cache-Control', 'private, no-store')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                if method != 'HEAD':
                    self.wfile.write(data)
            else:
                self._corsless_copy(e, e.read())
        except Exception as e:
            self.send_error(502, f"proxy: {e}")

    def _stream_video(self, resp, method):
        declared = resp.headers.get('Content-Length')
        if declared and (not declared.isdigit() or int(declared) > MAX_VIDEO_BYTES):
            self.send_error(413, 'Video exceeds 100 MB')
            return
        # Unknown lengths need explicit completion framing: a closed 200 response
        # alone would make a truncated prefix indistinguishable from valid media.
        chunked = not declared
        self.protocol_version = 'HTTP/1.1'
        self.close_connection = True
        self.send_response(resp.status)
        self.send_header('Connection', 'close')
        self.send_header('Content-Type', resp.headers.get('Content-Type', 'video/mp4'))
        self.send_header('Cache-Control', 'private, no-store')
        if declared:
            self.send_header('Content-Length', declared)
        else:
            self.send_header('Transfer-Encoding', 'chunked')
        self.end_headers()
        if method == 'HEAD':
            return
        total = 0
        try:
            while True:
                chunk = resp.read(min(65536, MAX_VIDEO_BYTES - total + 1))
                if not chunk:
                    if chunked:
                        self.wfile.write(b'0\r\n\r\n')
                        self.wfile.flush()
                    break
                if total + len(chunk) > MAX_VIDEO_BYTES:
                    # No terminating chunk: fetch/readers MUST reject the prefix.
                    break
                if chunked:
                    self.wfile.write(('%x\r\n' % len(chunk)).encode('ascii'))
                self.wfile.write(chunk)
                if chunked:
                    self.wfile.write(b'\r\n')
                self.wfile.flush()
                total += len(chunk)
        except Exception:
            # Headers are already sent. Never append a second HTTP/error body.
            self.close_connection = True

    def do_POST(self):
        if self.path.startswith("/v1/"):
            self._proxy("POST")
        else:
            self.send_error(404)

    def do_GET(self):
        if self.path.startswith("/v1/") or self.path == "/pricing.json":
            self._proxy("GET")
        else:
            super().do_GET()

    def _static_allowed(self):
        from urllib.parse import urlsplit, unquote
        from pathlib import Path
        path = urlsplit(self.path).path
        for _ in range(8):
            decoded = unquote(path)
            if decoded == path:
                break
            path = decoded
        if '%' in path or '\\' in path or '\x00' in path:
            return False
        parts = path.strip('/').split('/')
        if any(p in ('.', '..') or p.startswith('.') for p in parts if p):
            return False
        if path == '/':
            path = '/index.html'
        rel = path.lstrip('/')
        target = Path(ROOT) / rel
        if any(p.is_symlink() for p in [target, *target.parents] if p != Path(ROOT).parent):
            return False
        if not target.is_file() or not target.resolve().is_relative_to(Path(ROOT).resolve()):
            return False
        if target.suffix.lower() == '.py':
            return False
        return (rel in ('index.html', 'styles.css') or
                (rel.startswith('js/') and target.suffix == '.js') or
                (rel.startswith('skills/') and (target.name in ('singular.flow.json', 'singular.skill.json') or
                                               ('/prompts/' in rel and target.suffix == '.md'))))

    def send_head(self):
        if not self._static_allowed():
            self.send_error(404)
            return None
        return super().send_head()

    def do_HEAD(self):
        if self.path.startswith('/v1/') or self.path == '/pricing.json':
            self._proxy('HEAD')
        else:
            super().do_HEAD()

    def do_OPTIONS(self):
        # same-origin, so preflight shouldn't fire; answer politely anyway
        self.send_response(204)
        self.end_headers()

    def log_message(self, fmt, *args):
        sys.stderr.write("[shell] %s\n" % (fmt % args))

if __name__ == "__main__":
    port = int(os.environ.get("PORT") or (sys.argv[1] if len(sys.argv) > 1 else "8730"))
    print(f"Singular shell: http://0.0.0.0:{port}  (proxying /v1/* -> {GATEWAY})")
    http.server.ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
