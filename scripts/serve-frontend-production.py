#!/usr/bin/env python3
"""
Serve built Vite SPA from disk (stdlib only). Production Web-UI on :3001 — no Node/Vite at runtime.

- SPA fallback: unknown paths -> index.html (except /api/*)
- /api/* on this port: 404 + short hint (real API on backend :8000)
- No directory listings
"""

from __future__ import annotations

import argparse
import http.server
import os
import pathlib
import sys
import urllib.parse
from functools import partial
from http.server import ThreadingHTTPServer


def _safe_file_under_root(root: pathlib.Path, url_path: str) -> pathlib.Path | None:
    """Map URL path to a file under root; reject path traversal."""
    if not url_path or url_path.startswith("/"):
        rel = url_path.lstrip("/")
    else:
        rel = url_path
    if ".." in rel.split("/"):
        return None
    candidate = (root / rel).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


def resolve_public_path(root: pathlib.Path, path: str) -> pathlib.Path | None:
    """Return filesystem path to serve (SPA fallback to index.html). path = URL path only, no query."""
    path = path.split("?", 1)[0]
    path = urllib.parse.unquote(path)
    if not path.startswith("/"):
        path = "/" + path
    if path.startswith("/api"):
        return None
    root_r = root.resolve()
    if path == "/" or path == "":
        idx = root_r / "index.html"
        return idx if idx.is_file() else None
    cand = _safe_file_under_root(root_r, path)
    if cand is None:
        return None
    if cand.is_file():
        return cand
    idx = root_r / "index.html"
    return idx if idx.is_file() else None


class _SPAStaticHandler(http.server.SimpleHTTPRequestHandler):
    """Serves files from a fixed root with SPA fallback."""

    protocol_version = "HTTP/1.1"

    def __init__(self, *args, spa_root: pathlib.Path, **kwargs):
        self._spa_root = spa_root.resolve()
        super().__init__(*args, directory=str(self._spa_root), **kwargs)

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), fmt % args))

    def list_directory(self, path: str) -> bytes | None:  # noqa: ARG002
        self.send_error(403, "Directory listing disabled")
        return None

    def _send_api_not_here(self) -> None:
        body = (
            "Setuphelfer API is not served on this port.\n"
            "Use the backend on http://127.0.0.1:8000 (e.g. GET /api/version).\n"
        ).encode("utf-8")
        self.send_response(404)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)
        if path.startswith("/api"):
            self._send_api_not_here()
            return
        target = resolve_public_path(self._spa_root, path)
        if target is None:
            self.send_error(404, "Not found")
            return
        rel_url = "/" + str(target.relative_to(self._spa_root)).replace(os.sep, "/")
        old = self.path
        try:
            self.path = rel_url
            super().do_GET()
        finally:
            self.path = old

    def do_HEAD(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)
        if path.startswith("/api"):
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            return
        target = resolve_public_path(self._spa_root, path)
        if target is None:
            self.send_error(404, "Not found")
            return
        rel_url = "/" + str(target.relative_to(self._spa_root)).replace(os.sep, "/")
        old = self.path
        try:
            self.path = rel_url
            super().do_HEAD()
        finally:
            self.path = old


def main() -> int:
    p = argparse.ArgumentParser(description="Serve Setuphelfer frontend dist (SPA, stdlib only).")
    p.add_argument("--root", required=True, type=pathlib.Path, help="Path to frontend/dist")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=3001)
    args = p.parse_args()
    root = args.root.resolve()
    index = root / "index.html"
    if not index.is_file():
        print(f"ERROR: missing {index}", file=sys.stderr)
        return 1

    handler = partial(_SPAStaticHandler, spa_root=root)
    with ThreadingHTTPServer((args.host, args.port), handler) as httpd:
        httpd.allow_reuse_address = True
        print(f"Serving SPA from {root} at http://{args.host}:{args.port}/", flush=True)
        httpd.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
