"""Tiny app for the backend guard's self-test (playwright.config.ts here).

Standard library only, fake data only. The page fetches ?call=<url> on load;
the API answers:
- /api/ok       200;
- /api/warn     200, but logs an ERROR line;
- other /api/*  404.
"""

import json
import logging
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PAGE = b"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><link rel="icon" href="data:,"><title>Guard self-test</title></head>
<body><h1>Guard self-test</h1><script>
const call = new URLSearchParams(location.search).get('call');
if (call) fetch(call).catch(() => {});
</script></body></html>"""
log = logging.getLogger("guard-selftest")


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        # The page calls the API from another local origin too.
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/":
            self._send(200, PAGE, "text/html; charset=utf-8")
        elif path == "/api/ok":
            self._send(200, json.dumps({"ok": True}).encode(), "application/json")
        elif path == "/api/warn":
            log.error("guard self-test: something went wrong behind a 200 answer")
            self._send(200, json.dumps({"ok": True}).encode(), "application/json")
        else:
            self._send(404, json.dumps({"error": "not found"}).encode(), "application/json")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(levelname)s %(name)s: %(message)s")
    ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), Handler).serve_forever()
