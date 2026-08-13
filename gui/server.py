#!/usr/bin/env python3
"""
gui/server.py
Local web GUI for the Zebra label printer. Serves the animated
drag-and-drop page and a small JSON API that reuses zebra_core.py for
CSV parsing, ZPL generation, and raw printing. Stdlib only, no pip
installs -- matches the CLI's design.

Run:
  python gui/server.py
  (opens http://127.0.0.1:8934/ in your default browser)
"""

import json
import os
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from zebra_core import PRINTER_NAME, make_zpl, print_labels, read_labels_from_text

HOST = "127.0.0.1"
PORT = 8934
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # keep the console quiet

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/":
            path = "/index.html"
        safe_path = os.path.normpath(path).lstrip(os.sep)
        file_path = os.path.join(STATIC_DIR, safe_path)

        if not os.path.abspath(file_path).startswith(os.path.abspath(STATIC_DIR)):
            self.send_error(403)
            return
        if not os.path.isfile(file_path):
            self.send_error(404)
            return

        ext = os.path.splitext(file_path)[1]
        content_type = CONTENT_TYPES.get(ext, "application/octet-stream")
        with open(file_path, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path != "/api/print":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""
        try:
            body = json.loads(raw.decode("utf-8"))
        except Exception:
            self._send_json(400, {"ok": False, "error": "Bad request body."})
            return

        csv_text = body.get("csv", "")
        preview = bool(body.get("preview", False))

        overrides = body.get("overrides") or {}
        font_height_dots = overrides.get("font_height_dots")
        try:
            font_height_dots = int(font_height_dots) if font_height_dots else None
        except (TypeError, ValueError):
            font_height_dots = None
        h_align = overrides.get("h_align") or "C"
        v_align = overrides.get("v_align") or "C"

        try:
            labels = read_labels_from_text(csv_text)
        except Exception as e:
            self._send_json(400, {"ok": False, "error": f"Could not parse CSV: {e}"})
            return

        if not labels:
            self._send_json(400, {"ok": False, "error": "No values found in column B."})
            return

        if preview:
            self._send_json(200, {
                "ok": True,
                "preview": True,
                "count": len(labels),
                "labels": labels,
                "zpl_sample": make_zpl(labels[0], font_height_dots, h_align, v_align),
            })
            return

        try:
            print_labels(labels, PRINTER_NAME, font_height_dots, h_align, v_align)
        except Exception as e:
            self._send_json(500, {"ok": False, "error": str(e)})
            return

        self._send_json(200, {
            "ok": True,
            "preview": False,
            "count": len(labels),
            "labels": labels,
            "printer": PRINTER_NAME,
        })


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}/"

    def open_browser():
        time.sleep(0.4)
        webbrowser.open(url)

    threading.Thread(target=open_browser, daemon=True).start()
    print(f"Zebra GUI running at {url}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
