#!/usr/bin/env python3
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import urllib.request
import urllib.error

HOST = "127.0.0.1"
PORT = 8765
GITEA_BASE = "http://localhost:3000"
TOKEN_FILE = Path("token.txt")


def read_token():
    if not TOKEN_FILE.exists():
        return ""
    return TOKEN_FILE.read_text(encoding="utf-8").strip()


class Handler(SimpleHTTPRequestHandler):
    def _cors(self):
        origin = self.headers.get("Origin", "*")
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, Accept")

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        self._cors()
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            body = b'{"ok":true}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path.startswith("/gitea/"):
            return self._proxy()
        return super().do_GET()

    def do_POST(self):
        if self.path.startswith("/gitea/"):
            return self._proxy()
        self.send_error(405, "Method not allowed")

    def do_PUT(self):
        if self.path.startswith("/gitea/"):
            return self._proxy()
        self.send_error(405, "Method not allowed")

    def do_DELETE(self):
        if self.path.startswith("/gitea/"):
            return self._proxy()
        self.send_error(405, "Method not allowed")

    def _proxy(self):
        upstream_path = self.path[len("/gitea"):] or "/"
        target = GITEA_BASE.rstrip("/") + upstream_path

        body = None
        length = self.headers.get("Content-Length")
        if length:
            body = self.rfile.read(int(length))

        req = urllib.request.Request(target, data=body, method=self.command)
        req.add_header("Accept", self.headers.get("Accept", "application/json"))

        token = read_token()
        if token:
            req.add_header("Authorization", f"token {token}")

        if "Content-Type" in self.headers:
            req.add_header("Content-Type", self.headers["Content-Type"])

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = resp.read()
                self.send_response(resp.status)
                self.send_header("Content-Type", resp.headers.get("Content-Type", "application/json"))
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
        except urllib.error.HTTPError as e:
            payload = e.read() if hasattr(e, "read") else b""
            self.send_response(e.code)
            self.send_header("Content-Type", e.headers.get("Content-Type", "application/json"))
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            if payload:
                self.wfile.write(payload)
        except Exception as e:
            msg = ('{"error":"%s"}' % str(e).replace('"', '\\"')).encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)


if __name__ == "__main__":
    print(f"Serving at http://{HOST}:{PORT}")
    print(f"Proxy: http://{HOST}:{PORT}/gitea/* -> {GITEA_BASE}/*")
    print(f"Token file: {TOKEN_FILE.resolve()}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
