"""Demo app for the browser QA self-test: static pages plus a tiny JSON API.

Standard library only, fake data only. The endpoints exist to prove the
backend guard in project-starter/e2e/fixtures.ts:
- GET/POST /api/invoices  a working API with in-memory state (check R2);
- GET /api/warn           answers 200 but logs an ERROR line;
- anything else under /api/ answers 404.
"""

import json
import logging
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
INVOICES: list[dict] = []
log = logging.getLogger("demo")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(HERE), **kwargs)

    def _json(self, status: int, body) -> None:
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/api/invoices":
            self._json(200, INVOICES)
        elif self.path == "/api/warn":
            log.error("demo: something went wrong behind a 200 answer")
            self._json(200, {"ok": True})
        elif self.path.startswith("/api/"):
            self._json(404, {"error": "not found"})
        else:
            super().do_GET()

    def do_POST(self):
        if self.path != "/api/invoices":
            self._json(404, {"error": "not found"})
            return
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        invoice = {"number": str(body["number"]), "amount": str(body["amount"])}
        INVOICES.append(invoice)
        self._json(201, invoice)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(levelname)s %(name)s: %(message)s")
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
