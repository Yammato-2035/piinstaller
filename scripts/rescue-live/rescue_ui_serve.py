#!/usr/bin/env python3
"""
Rescue kiosk UI server: static files from UI root + reverse proxy /api/* → backend :8000.

Replaces ``python3 -m http.server`` on port 8765 so Chromium same-origin fetches reach the backend.
"""

from __future__ import annotations

import argparse
import http.server
import os
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request
from functools import partial
from http.server import ThreadingHTTPServer
from typing import ClassVar

FORWARD_REQUEST_HEADERS = frozenset(
    {
        "content-type",
        "content-length",
        "authorization",
        "accept",
        "accept-encoding",
        "user-agent",
        "cache-control",
    }
)


def _safe_file_under_root(root: pathlib.Path, url_path: str) -> pathlib.Path | None:
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
    path = path.split("?", 1)[0]
    path = urllib.parse.unquote(path)
    if not path.startswith("/"):
        path = "/" + path
    if path.startswith("/api"):
        return None
    root_r = root.resolve()
    if path in ("/", ""):
        idx = root_r / "rescue.html"
        if idx.is_file():
            return idx
        idx = root_r / "index.html"
        return idx if idx.is_file() else None
    cand = _safe_file_under_root(root_r, path)
    if cand is None:
        return None
    if cand.is_file():
        return cand
    for fallback in ("rescue.html", "index.html"):
        idx = root_r / fallback
        if idx.is_file():
            return idx
    return None


class RescueUIHandler(http.server.SimpleHTTPRequestHandler):
    """Serve rescue static UI and proxy API to local backend."""

    protocol_version = "HTTP/1.1"
    upstream: ClassVar[str] = "http://127.0.0.1:8000"

    def __init__(self, *args, spa_root: pathlib.Path, upstream: str, **kwargs):
        self._spa_root = spa_root.resolve()
        self.upstream = upstream.rstrip("/")
        super().__init__(*args, directory=str(self._spa_root), **kwargs)

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), fmt % args))

    def list_directory(self, path: str) -> bytes | None:  # noqa: ARG002
        self.send_error(403, "Directory listing disabled")
        return None

    def _proxy_api(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        upstream_url = f"{self.upstream}{parsed.path}"
        if parsed.query:
            upstream_url = f"{upstream_url}?{parsed.query}"

        content_length = int(self.headers.get("Content-Length", "0") or "0")
        body = self.rfile.read(content_length) if content_length > 0 else None

        headers = {
            k: v
            for k, v in self.headers.items()
            if k.lower() in FORWARD_REQUEST_HEADERS
        }
        req = urllib.request.Request(
            upstream_url,
            data=body,
            headers=headers,
            method=self.command,
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                self.send_response(resp.status)
                for key, val in resp.headers.items():
                    lk = key.lower()
                    if lk in ("transfer-encoding", "connection"):
                        continue
                    self.send_header(key, val)
                self.end_headers()
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
        except urllib.error.HTTPError as exc:
            self.send_response(exc.code)
            for key, val in exc.headers.items():
                lk = key.lower()
                if lk in ("transfer-encoding", "connection"):
                    continue
                self.send_header(key, val)
            self.end_headers()
            err_body = exc.read()
            if err_body:
                self.wfile.write(err_body)
        except urllib.error.URLError as exc:
            body = f"Rescue API upstream unreachable: {exc.reason}\n".encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def _serve_static(self, method: str) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)
        target = resolve_public_path(self._spa_root, path)
        if target is None:
            self.send_error(404, "Not found")
            return
        rel_url = "/" + str(target.relative_to(self._spa_root)).replace(os.sep, "/")
        old = self.path
        try:
            self.path = rel_url
            if method == "HEAD":
                super().do_HEAD()
            else:
                super().do_GET()
        finally:
            self.path = old

    def do_GET(self) -> None:  # noqa: N802
        if urllib.parse.urlparse(self.path).path.startswith("/api"):
            self._proxy_api()
            return
        self._serve_static("GET")

    def do_HEAD(self) -> None:  # noqa: N802
        if urllib.parse.urlparse(self.path).path.startswith("/api"):
            self._proxy_api()
            return
        self._serve_static("HEAD")

    def do_POST(self) -> None:  # noqa: N802
        if urllib.parse.urlparse(self.path).path.startswith("/api"):
            self._proxy_api()
            return
        self.send_error(405, "Method not allowed")

    def do_PUT(self) -> None:  # noqa: N802
        if urllib.parse.urlparse(self.path).path.startswith("/api"):
            self._proxy_api()
            return
        self.send_error(405, "Method not allowed")

    def do_PATCH(self) -> None:  # noqa: N802
        if urllib.parse.urlparse(self.path).path.startswith("/api"):
            self._proxy_api()
            return
        self.send_error(405, "Method not allowed")

    def do_DELETE(self) -> None:  # noqa: N802
        if urllib.parse.urlparse(self.path).path.startswith("/api"):
            self._proxy_api()
            return
        self.send_error(405, "Method not allowed")

    def do_OPTIONS(self) -> None:  # noqa: N802
        if urllib.parse.urlparse(self.path).path.startswith("/api"):
            self._proxy_api()
            return
        self.send_response(204)
        self.end_headers()


def main() -> int:
    p = argparse.ArgumentParser(description="Rescue UI static server with /api proxy.")
    p.add_argument("--root", required=True, type=pathlib.Path, help="Path to rescue UI root")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--upstream", default=os.environ.get("SETUPHELFER_RESCUE_API_UPSTREAM", "http://127.0.0.1:8000"))
    args = p.parse_args()
    root = args.root.resolve()
    if not (root / "rescue.html").is_file() and not (root / "index.html").is_file():
        print(f"ERROR: missing rescue.html or index.html under {root}", file=sys.stderr)
        return 1

    handler = partial(RescueUIHandler, spa_root=root, upstream=args.upstream)
    with ThreadingHTTPServer((args.host, args.port), handler) as httpd:
        httpd.allow_reuse_address = True
        print(
            f"Rescue UI at http://{args.host}:{args.port}/ (api → {args.upstream})",
            flush=True,
        )
        httpd.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
