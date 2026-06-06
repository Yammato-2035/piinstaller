"""Rescue telemetry LAN proxy — allowlist, status, and forwarding tests."""

from __future__ import annotations

import json
import os
import socket
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.rescue_telemetry_lan_proxy import (  # noqa: E402
    ALLOWED_ROUTES,
    RescueTelemetryLanProxyHandler,
    build_compact_telemetry_lan_proxy_status,
    build_status_payload,
    detect_lan_ip,
    is_path_allowed,
    is_port_free,
    read_pid_file,
    run_server,
)

try:
    import urllib.error
    import urllib.request
except ImportError:
    pass


class _MockUpstreamHandler(BaseHTTPRequestHandler):
    def log_message(self, _format: str, *_args) -> None:
        return

    def do_GET(self) -> None:
        if self.path.startswith("/api/rescue/telemetry/health"):
            body = json.dumps({"status": "ok", "ingest_enabled": True}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0") or "0")
        _ = self.rfile.read(length) if length else b""
        if self.path.startswith("/api/rescue/telemetry/v1/ingest"):
            body = json.dumps({"accepted": True}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()


def _free_port() -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


class RescueTelemetryLanProxyAllowlistTests(unittest.TestCase):
    def test_allowed_paths_only_telemetry(self) -> None:
        self.assertTrue(is_path_allowed("GET", "/api/rescue/telemetry/health"))
        self.assertTrue(is_path_allowed("POST", "/api/rescue/telemetry/v1/ingest"))
        self.assertTrue(is_path_allowed("OPTIONS", "/api/rescue/telemetry/health"))
        self.assertFalse(is_path_allowed("GET", "/api/version"))
        self.assertFalse(is_path_allowed("GET", "/openapi.json"))
        self.assertFalse(is_path_allowed("GET", "/api/dev-dashboard/status"))
        self.assertFalse(is_path_allowed("POST", "/api/rescue/telemetry/v1/ingest/extra"))

    def test_allowed_routes_set_size(self) -> None:
        self.assertEqual(len(ALLOWED_ROUTES), 4)


class RescueTelemetryLanProxyStatusTests(unittest.TestCase):
    def test_status_payload_no_secrets(self) -> None:
        payload = build_status_payload(
            running=False,
            pid=None,
            bind_host="192.168.1.10",
            port=8001,
            upstream="http://127.0.0.1:8000",
            backend_health_ok=True,
            lan_health_ok=False,
        )
        dumped = json.dumps(payload)
        self.assertFalse(payload["secrets_exposed"])
        self.assertNotIn("token", dumped.lower())
        self.assertIn("health_url", payload)
        self.assertIn("ingest_url", payload)
        self.assertTrue(payload["allowed_paths_only"])

    def test_compact_status_shape(self) -> None:
        with patch("core.rescue_telemetry_lan_proxy.read_pid_file", return_value=None):
            with patch("core.rescue_telemetry_lan_proxy.backend_local_health_ok", return_value=True):
                body = build_compact_telemetry_lan_proxy_status()
        self.assertTrue(body.get("configured"))
        self.assertFalse(body.get("running"))
        self.assertIn("next_step", body)
        self.assertFalse(body.get("secrets_exposed"))


class RescueTelemetryLanProxyIntegrationTests(unittest.TestCase):
    def test_proxy_blocks_non_telemetry_paths(self) -> None:
        upstream_port = _free_port()
        proxy_port = _free_port()
        upstream = HTTPServer(("127.0.0.1", upstream_port), _MockUpstreamHandler)
        upstream_thread = threading.Thread(target=upstream.serve_forever, daemon=True)
        upstream_thread.start()
        RescueTelemetryLanProxyHandler.upstream_base = f"http://127.0.0.1:{upstream_port}"
        proxy_thread = threading.Thread(
            target=run_server,
            args=("127.0.0.1", proxy_port, f"http://127.0.0.1:{upstream_port}"),
            daemon=True,
        )
        proxy_thread.start()
        import time

        time.sleep(0.3)

        def _get(path: str) -> int:
            url = f"http://127.0.0.1:{proxy_port}{path}"
            try:
                with urllib.request.urlopen(url, timeout=3) as resp:
                    return resp.status
            except urllib.error.HTTPError as exc:
                return exc.code

        self.assertEqual(_get("/api/rescue/telemetry/health"), 200)
        self.assertEqual(_get("/api/version"), 404)
        self.assertEqual(_get("/openapi.json"), 404)
        self.assertEqual(_get("/api/dev-dashboard/status"), 404)
        upstream.shutdown()


class RescueTelemetryLanProxyUtilityTests(unittest.TestCase):
    def test_detect_lan_ip_skips_loopback(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_RESCUE_TELEMETRY_BIND": "127.0.0.1"}, clear=False):
            with patch(
                "core.rescue_telemetry_lan_proxy.subprocess.check_output",
                return_value="1.1.1.1 via default src 192.168.178.140 uid",
            ):
                ip = detect_lan_ip()
        self.assertEqual(ip, "192.168.178.140")

    def test_read_pid_file_missing(self) -> None:
        with patch("core.rescue_telemetry_lan_proxy.PID_FILE") as mock_pid:
            mock_pid.is_file.return_value = False
            self.assertIsNone(read_pid_file())

    def test_is_port_free_on_ephemeral(self) -> None:
        port = _free_port()
        self.assertTrue(is_port_free(port, "127.0.0.1"))


class CompactStatusTelemetryLanProxyFieldTests(unittest.TestCase):
    def test_build_compact_dcc_includes_telemetry_lan_proxy(self) -> None:
        from core.dev_dashboard_compact_status import build_compact_dcc_status

        with patch.dict(os.environ, {"SETUPHELFER_INSTALL_PROFILE": "release"}, clear=False):
            body = build_compact_dcc_status(
                request_headers={},
                backend_runtime_path="/opt/setuphelfer/backend",
            )
        proxy = (body.get("rescue") or {}).get("telemetry_lan_proxy") or {}
        self.assertTrue(proxy.get("configured"))
        self.assertIn("health_url", proxy)
        self.assertFalse(proxy.get("secrets_exposed"))


if __name__ == "__main__":
    unittest.main()
