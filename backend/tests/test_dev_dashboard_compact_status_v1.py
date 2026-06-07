"""Compact DCC status endpoint tests."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.dev_dashboard_compact_status import (  # noqa: E402
    _detect_usb_rescue_mount,
    build_compact_dcc_status,
)

try:
    from fastapi.testclient import TestClient

    from app import app as fastapi_app

    _HAS_TC = True
except Exception:
    TestClient = None  # type: ignore[misc, assignment]
    fastapi_app = None  # type: ignore[misc, assignment]
    _HAS_TC = False


class CompactStatusCoreTests(unittest.TestCase):
    def test_compact_payload_has_no_secrets(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SETUPHELFER_INSTALL_PROFILE": "release",
                "DCC_DEVELOPER_ENABLED": "1",
                "DCC_DEVELOPER_TOKEN": "hidden-token-value",
            },
            clear=False,
        ):
            body = build_compact_dcc_status(
                request_headers={"X-Setuphelfer-Developer-Token": "hidden-token-value"},
                backend_runtime_path="/opt/setuphelfer/backend",
            )
        dumped = str(body)
        self.assertNotIn("hidden-token-value", dumped)
        self.assertTrue(body.get("compact"))
        self.assertTrue(body.get("dcc_visible"))
        rescue = body.get("rescue") or {}
        usb_op = rescue.get("usb_operator") or {}
        self.assertIn("usb_detected", usb_op)
        self.assertIn("destructive_write_allowed", usb_op)
        proxy = rescue.get("telemetry_lan_proxy") or {}
        self.assertTrue(proxy.get("configured"))
        self.assertIn("health_url", proxy)
        self.assertFalse(proxy.get("secrets_exposed"))
        net_tel = rescue.get("network_telemetry") or {}
        self.assertIn("last_ack_id", net_tel)
        self.assertIn("last_ingest_at", net_tel)
        self.assertIn("start_assistant_autostart_validated", net_tel)

    def test_compact_includes_dev_server_when_capability_allows(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SETUPHELFER_INSTALL_PROFILE": "release",
                "DCC_DEVELOPER_ENABLED": "1",
                "DCC_DEVELOPER_TOKEN": "hidden-token-value",
            },
            clear=False,
        ):
            body = build_compact_dcc_status(
                request_headers={"X-Setuphelfer-Developer-Token": "hidden-token-value"},
                backend_runtime_path="/opt/setuphelfer/backend",
            )
        dev = body.get("dev_server") or {}
        self.assertTrue(dev.get("host_locally_allowed"))
        self.assertTrue(dev.get("enabled"))
        self.assertEqual(dev.get("mode"), "local_lab")

    def test_detect_usb_mount_skips_inaccessible_paths(self) -> None:
        class _BlockedPath:
            def __init__(self, raw: str) -> None:
                self._raw = raw

            def is_dir(self) -> bool:
                if "volker" in self._raw:
                    raise PermissionError(13, "Permission denied")
                return False

        with patch("core.dev_dashboard_compact_status.Path", side_effect=_BlockedPath):
            result = _detect_usb_rescue_mount()
        self.assertFalse(result["detected"])
        self.assertIsNone(result["mount_path"])


@unittest.skipUnless(_HAS_TC, "FastAPI TestClient nicht verfügbar")
class CompactStatusHttpTests(unittest.TestCase):
    def test_release_compact_status_without_token_via_capability(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_INSTALL_PROFILE": "release"}, clear=False):
            client = TestClient(fastapi_app, base_url="http://localhost")
            r = client.get("/api/dev-dashboard/compact-status")
            self.assertEqual(r.status_code, 200)
            self.assertTrue(r.json().get("compact"))

    def test_release_status_with_token_not_profile_blocked_body(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SETUPHELFER_INSTALL_PROFILE": "release",
                "DCC_DEVELOPER_ENABLED": "1",
                "DCC_DEVELOPER_TOKEN": "valid-token",
            },
            clear=False,
        ):
            client = TestClient(fastapi_app, base_url="http://localhost")
            r = client.get(
                "/api/dev-dashboard/status",
                headers={"X-Setuphelfer-Developer-Token": "valid-token"},
            )
            self.assertEqual(r.status_code, 200)
            self.assertNotEqual(r.json().get("code"), "PROFILE_ROUTE_BLOCKED")
            self.assertNotIn("valid-token", r.text)

    def test_wrong_token_still_blocked(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SETUPHELFER_INSTALL_PROFILE": "release",
                "DCC_DEVELOPER_ENABLED": "1",
                "DCC_DEVELOPER_TOKEN": "valid-token",
            },
            clear=False,
        ):
            client = TestClient(fastapi_app, base_url="http://localhost")
            r = client.get(
                "/api/dev-dashboard/status",
                headers={"X-Setuphelfer-Developer-Token": "wrong-token"},
            )
            self.assertEqual(r.status_code, 404)


if __name__ == "__main__":
    unittest.main()
