"""Rescue telemetry LAN proxy — allowlisted forwarder to local backend only."""

from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

DEFAULT_PORT = 8001
DEFAULT_UPSTREAM = "http://127.0.0.1:8000"
DEFAULT_BIND_ENV = "SETUPHELFER_RESCUE_TELEMETRY_BIND"
DEFAULT_PORT_ENV = "SETUPHELFER_RESCUE_TELEMETRY_PORT"
DEFAULT_UPSTREAM_ENV = "SETUPHELFER_RESCUE_TELEMETRY_UPSTREAM"
PID_FILE = Path("/tmp/setuphelfer-rescue-telemetry-lan-proxy.pid")

ALLOWED_ROUTES: frozenset[tuple[str, str]] = frozenset(
    {
        ("GET", "/api/rescue/telemetry/health"),
        ("POST", "/api/rescue/telemetry/v1/ingest"),
        ("OPTIONS", "/api/rescue/telemetry/health"),
        ("OPTIONS", "/api/rescue/telemetry/v1/ingest"),
    }
)

TASK_PULL_ROUTES: frozenset[tuple[str, str]] = frozenset(
    {
        ("GET", "/api/rescue/telemetry/v1/tasks/next"),
        ("POST", "/api/rescue/telemetry/v1/tasks/result"),
        ("OPTIONS", "/api/rescue/telemetry/v1/tasks/next"),
        ("OPTIONS", "/api/rescue/telemetry/v1/tasks/result"),
    }
)


def effective_allowed_routes() -> frozenset[tuple[str, str]]:
    routes = set(ALLOWED_ROUTES)
    if os.environ.get("SETUPHELFER_RESCUE_TELEMETRY_TASK_PULL_ENABLED", "1").strip().lower() in {
        "1",
        "true",
        "yes",
    }:
        routes.update(TASK_PULL_ROUTES)
    return frozenset(routes)

FORWARD_REQUEST_HEADERS = frozenset(
    {
        "content-type",
        "content-length",
        "authorization",
        "x-setuphelfer-rescue-telemetry-token",
        "x-setuphelfer-telemetry-hmac",
        "accept",
        "accept-encoding",
        "user-agent",
    }
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def status_json_path() -> Path:
    return repo_root() / "docs/evidence/runtime-results/rescue/rescue_telemetry_lan_proxy_status_latest.json"


def log_file_path() -> Path:
    return repo_root() / "docs/evidence/runtime-results/rescue/rescue_telemetry_lan_proxy_latest.log"


def detect_lan_ip() -> str | None:
    bind_override = os.environ.get(DEFAULT_BIND_ENV, "").strip()
    if bind_override and bind_override not in {"127.0.0.1", "localhost"}:
        return bind_override
    try:
        out = subprocess.check_output(
            ["ip", "-4", "route", "get", "1.1.1.1"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=3,
        )
        parts = out.split()
        for idx, token in enumerate(parts):
            if token == "src" and idx + 1 < len(parts):
                candidate = parts[idx + 1]
                if _is_usable_lan_ip(candidate):
                    return candidate
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    try:
        out = subprocess.check_output(["hostname", "-I"], text=True, timeout=3)
        for candidate in out.split():
            if _is_usable_lan_ip(candidate):
                return candidate
    except (OSError, subprocess.SubprocessError, ValueError):
        pass
    return None


def _is_usable_lan_ip(ip: str) -> bool:
    if not ip or ip.startswith("127."):
        return False
    if ip.startswith("169.254."):
        return False
    if ip.startswith("172.17.") or ip.startswith("172.18.") or ip.startswith("172.19."):
        return False
    if ip.startswith("10.0.2."):
        return False
    return bool(re.match(r"^\d+\.\d+\.\d+\.\d+$", ip))


def is_path_allowed(method: str, path: str) -> bool:
    normalized = path.split("?", 1)[0]
    if not normalized.startswith("/"):
        normalized = f"/{normalized}"
    return (method.upper(), normalized) in effective_allowed_routes()


def health_url(bind_host: str, port: int) -> str:
    return f"http://{bind_host}:{port}/api/rescue/telemetry/health"


def ingest_url(bind_host: str, port: int) -> str:
    return f"http://{bind_host}:{port}/api/rescue/telemetry/v1/ingest"


def read_pid_file() -> int | None:
    if not PID_FILE.is_file():
        return None
    try:
        raw = PID_FILE.read_text(encoding="utf-8").strip()
        pid = int(raw)
    except (OSError, ValueError):
        return None
    try:
        os.kill(pid, 0)
    except OSError:
        return None
    return pid


def is_port_free(port: int, bind_host: str = "0.0.0.0") -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((bind_host, port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def backend_local_health_ok(upstream: str = DEFAULT_UPSTREAM, timeout: float = 3.0) -> bool:
    url = f"{upstream.rstrip('/')}/api/rescue/telemetry/health"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            if resp.status != 200:
                return False
            body = json.loads(resp.read().decode("utf-8", errors="replace"))
            return body.get("status") == "ok"
    except (urllib.error.URLError, OSError, json.JSONDecodeError, ValueError):
        return False


def probe_lan_health(bind_host: str, port: int, timeout: float = 3.0) -> bool:
    url = health_url(bind_host, port)
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status == 200
    except (urllib.error.URLError, OSError):
        return False


def append_proxy_log(method: str, path: str, status: int, remote_addr: str) -> None:
    log_path = log_file_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    line = f"{ts} method={method} path={path} status={status} remote={remote_addr}\n"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(line)


def write_status_file(payload: dict[str, Any]) -> None:
    path = status_json_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_status_payload(
    *,
    running: bool,
    pid: int | None,
    bind_host: str | None,
    port: int,
    upstream: str,
    backend_health_ok: bool,
    lan_health_ok: bool,
    blockers: list[str] | None = None,
    error_code: str | None = None,
) -> dict[str, Any]:
    host = bind_host or "unknown"
    return {
        "schema_version": 1,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "running": running,
        "pid": pid,
        "bind_host": bind_host,
        "bind_port": port,
        "upstream": upstream,
        "health_url": health_url(host, port) if bind_host else None,
        "ingest_url": ingest_url(host, port) if bind_host else None,
        "backend_health_ok": backend_health_ok,
        "lan_health_ok": lan_health_ok,
        "allowed_paths": sorted({path for _method, path in effective_allowed_routes()}),
        "allowed_paths_only": True,
        "blockers": blockers or [],
        "error_code": error_code,
        "secrets_exposed": False,
    }


def build_compact_telemetry_lan_proxy_status() -> dict[str, Any]:
    port = int(os.environ.get(DEFAULT_PORT_ENV, str(DEFAULT_PORT)))
    upstream = os.environ.get(DEFAULT_UPSTREAM_ENV, DEFAULT_UPSTREAM).strip() or DEFAULT_UPSTREAM
    bind_host = detect_lan_ip()
    pid = read_pid_file()
    running = pid is not None
    backend_ok = backend_local_health_ok(upstream)
    lan_ok = probe_lan_health(bind_host, port) if running and bind_host else False
    blockers: list[str] = []
    if not backend_ok:
        blockers.append("BACKEND_HEALTH_FAILED")
    if running and not lan_ok:
        blockers.append("LAN_HEALTH_FAILED")
    if not running:
        blockers.append("PROXY_NOT_RUNNING")
    next_step = (
        "MSI Live-System: curl health_url; Telemetrie-Ingest senden."
        if running and lan_ok and backend_ok
        else "Operator: ./scripts/rescue-live/start-rescue-telemetry-lan-proxy.sh"
    )
    return {
        "configured": True,
        "running": running,
        "bind_host": bind_host,
        "bind_port": port,
        "health_url": health_url(bind_host, port) if bind_host else None,
        "ingest_url": ingest_url(bind_host, port) if bind_host else None,
        "backend_local_health_ok": backend_ok,
        "lan_health_ok": lan_ok,
        "allowed_paths_only": True,
        "allowed_paths": sorted({path for _method, path in effective_allowed_routes()}),
        "next_step": next_step,
        "blockers": blockers,
        "secrets_exposed": False,
    }


class RescueTelemetryLanProxyHandler(BaseHTTPRequestHandler):
    upstream_base: str = DEFAULT_UPSTREAM
    log_lock: threading.Lock = threading.Lock()

    def log_message(self, _format: str, *_args: Any) -> None:
        return

    def _remote_addr(self) -> str:
        return self.client_address[0] if self.client_address else "unknown"

    def _reject(self, method: str, path: str, status: int = 404) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"detail": "path not allowed on rescue telemetry LAN proxy"}).encode("utf-8"))
        with self.log_lock:
            append_proxy_log(method, path, status, self._remote_addr())

    def _proxy(self, method: str) -> None:
        parsed = urlparse(self.path)
        path = parsed.path or "/"
        if not is_path_allowed(method, path):
            self._reject(method, path, 404)
            return
        upstream_url = f"{self.upstream_base.rstrip('/')}{path}"
        if parsed.query:
            upstream_url = f"{upstream_url}?{parsed.query}"
        body = b""
        if method in {"POST", "PUT", "PATCH"}:
            length = int(self.headers.get("Content-Length", "0") or "0")
            body = self.rfile.read(length) if length > 0 else b""
        headers = {}
        for key, value in self.headers.items():
            if key.lower() in FORWARD_REQUEST_HEADERS:
                headers[key] = value
        req = urllib.request.Request(upstream_url, data=body if body else None, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = resp.read()
                status = resp.status
                self.send_response(status)
                for header, value in resp.headers.items():
                    lowered = header.lower()
                    if lowered in {"transfer-encoding", "connection"}:
                        continue
                    self.send_header(header, value)
                self.end_headers()
                self.wfile.write(payload)
                with self.log_lock:
                    append_proxy_log(method, path, status, self._remote_addr())
        except urllib.error.HTTPError as exc:
            payload = exc.read()
            self.send_response(exc.code)
            for header, value in exc.headers.items():
                lowered = header.lower()
                if lowered in {"transfer-encoding", "connection"}:
                    continue
                self.send_header(header, value)
            self.end_headers()
            self.wfile.write(payload)
            with self.log_lock:
                append_proxy_log(method, path, exc.code, self._remote_addr())
        except (urllib.error.URLError, OSError):
            self._reject(method, path, 502)

    def do_GET(self) -> None:
        self._proxy("GET")

    def do_POST(self) -> None:
        self._proxy("POST")

    def do_OPTIONS(self) -> None:
        self._proxy("OPTIONS")


def run_server(bind_host: str, port: int, upstream: str) -> None:
    RescueTelemetryLanProxyHandler.upstream_base = upstream
    server = ThreadingHTTPServer((bind_host, port), RescueTelemetryLanProxyHandler)
    server.daemon_threads = True
    try:
        server.serve_forever()
    finally:
        server.server_close()


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Setuphelfer rescue telemetry LAN proxy")
    parser.add_argument("--bind", default=os.environ.get(DEFAULT_BIND_ENV, "") or detect_lan_ip())
    parser.add_argument("--port", type=int, default=int(os.environ.get(DEFAULT_PORT_ENV, str(DEFAULT_PORT))))
    parser.add_argument("--upstream", default=os.environ.get(DEFAULT_UPSTREAM_ENV, DEFAULT_UPSTREAM))
    args = parser.parse_args(argv)
    if not args.bind:
        print("ERROR: LAN bind IP not detected; set SETUPHELFER_RESCUE_TELEMETRY_BIND", file=sys.stderr)
        return 2
    if read_pid_file() is not None:
        print(f"ERROR: proxy already running pid={read_pid_file()}", file=sys.stderr)
        return 3
    if not is_port_free(args.port, args.bind):
        print(f"ERROR: port {args.port} not free on {args.bind}", file=sys.stderr)
        return 4
    if not backend_local_health_ok(args.upstream):
        print("ERROR: backend telemetry health not ok on upstream", file=sys.stderr)
        return 5
    PID_FILE.write_text(f"{os.getpid()}\n", encoding="utf-8")
    write_status_file(
        build_status_payload(
            running=True,
            pid=os.getpid(),
            bind_host=args.bind,
            port=args.port,
            upstream=args.upstream,
            backend_health_ok=True,
            lan_health_ok=False,
        )
    )
    print(f"OK: rescue telemetry LAN proxy bind={args.bind}:{args.port} upstream={args.upstream}")
    run_server(args.bind, args.port, args.upstream)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
