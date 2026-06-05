"""Rescue telemetry ingest — separate from DCC, not PROFILE_ROUTE_BLOCKED."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.rescue_telemetry_ingest import (  # noqa: E402
    compute_payload_hash,
    load_rescue_telemetry_ingest_config,
    process_telemetry_ingest,
)
from core.install_profile import path_allowed_for_active_profile  # noqa: E402

try:
    from fastapi.testclient import TestClient

    from app import app as fastapi_app

    _HAS_TC = True
except Exception:
    TestClient = None  # type: ignore[misc, assignment]
    fastapi_app = None  # type: ignore[misc, assignment]
    _HAS_TC = False


def _minimal_envelope(**overrides: object) -> dict:
    payload = {
        "schema_version": "1.0.0",
        "run_id": "win-inspect-test-001",
        "device_session_id": "devsess-test-001",
        "created_at": "2026-06-05T13:30:00+02:00",
        "source": "rescue_stick",
        "payload_kind": "windows_rescue_inspect",
        "privacy_level": "diagnostic_metadata",
        "contains_personal_data": False,
        "operator_consent_state": "not_required_for_diagnostic_metadata",
        "diagnostics": {"codes": ["WIN-INSPECT-001"], "severity": "info", "recommended_actions": []},
    }
    payload.update(overrides)
    payload["payload_hash_sha256"] = compute_payload_hash(payload)
    return payload


class RescueTelemetryIngestCoreTests(unittest.TestCase):
    def test_compute_payload_hash_excludes_self_field(self) -> None:
        env = _minimal_envelope()
        declared = env["payload_hash_sha256"]
        without = {k: v for k, v in env.items() if k != "payload_hash_sha256"}
        env2 = dict(without)
        env2["payload_hash_sha256"] = compute_payload_hash(without)
        self.assertEqual(env2["payload_hash_sha256"], declared)

    def test_disabled_returns_503(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cfg = load_rescue_telemetry_ingest_config()
            cfg = cfg.__class__(
                enabled=False,
                ingest_token_configured=False,
                hmac_required=False,
                storage_root=Path(td),
                queue_dir=Path(td) / "queue",
                ingest_dir=Path(td) / "received",
                ack_dir=Path(td) / "acks",
            )
            result = process_telemetry_ingest(
                _minimal_envelope(),
                headers={},
                body_bytes=b"{}",
                config=cfg,
            )
            self.assertEqual(result["http_status"], 503)
            self.assertEqual(result["body"]["code"], "TELEMETRY-DISABLED-001")

    def test_enabled_ack_with_hash_match(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = load_rescue_telemetry_ingest_config().__class__(
                enabled=True,
                ingest_token_configured=False,
                hmac_required=False,
                storage_root=root,
                queue_dir=root / "queue",
                ingest_dir=root / "received",
                ack_dir=root / "acks",
            )
            envelope = _minimal_envelope()
            raw = json.dumps(envelope, sort_keys=True).encode("utf-8")
            result = process_telemetry_ingest(
                envelope,
                headers={"X-Setuphelfer-Payload-Hash": envelope["payload_hash_sha256"]},
                body_bytes=raw,
                config=cfg,
            )
            self.assertEqual(result["http_status"], 200)
            self.assertEqual(result["body"]["status"], "acknowledged")
            self.assertTrue(result["body"]["hash_match"])
            self.assertEqual(result["body"]["payload_hash_sha256"], envelope["payload_hash_sha256"])

    def test_hash_mismatch_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = load_rescue_telemetry_ingest_config().__class__(
                enabled=True,
                ingest_token_configured=False,
                hmac_required=False,
                storage_root=root,
                queue_dir=root / "queue",
                ingest_dir=root / "received",
                ack_dir=root / "acks",
            )
            envelope = _minimal_envelope()
            envelope["payload_hash_sha256"] = "0" * 64
            result = process_telemetry_ingest(envelope, headers={}, body_bytes=b"{}", config=cfg)
            self.assertEqual(result["http_status"], 409)
            self.assertEqual(result["body"]["code"], "TELEMETRY-HASH-001")


@unittest.skipUnless(_HAS_TC, "FastAPI TestClient nicht verfügbar")
class RescueTelemetryIngestHttpTests(unittest.TestCase):
    def _client_env(self, tmp: str, *, enabled: str = "1", token: str = "") -> dict[str, str]:
        return {
            "SETUPHELFER_INSTALL_PROFILE": "release",
            "RESCUE_TELEMETRY_INGEST_ENABLED": enabled,
            "RESCUE_TELEMETRY_INGEST_STORAGE_ROOT": tmp,
            "RESCUE_TELEMETRY_INGEST_TOKEN": token,
        }

    def test_release_profile_blocks_dcc_not_telemetry_health(self) -> None:
        with tempfile.TemporaryDirectory() as td, patch.dict(
            os.environ, self._client_env(td, enabled="0"), clear=False
        ):
            client = TestClient(fastapi_app, base_url="http://localhost")
            dcc = client.get("/api/dev-dashboard/status")
            self.assertEqual(dcc.status_code, 404)
            self.assertEqual(dcc.json().get("code"), "PROFILE_ROUTE_BLOCKED")
            cap = client.get("/api/dev-dashboard/capability-status")
            self.assertEqual(cap.status_code, 200)
            self.assertIn("reason", cap.json())
            health = client.get("/api/rescue/telemetry/health")
            self.assertEqual(health.status_code, 200)
            body = health.json()
            self.assertEqual(body["service"], "rescue_telemetry_ingest")
            self.assertFalse(body["dcc_required"])
            self.assertTrue(body["profile_gate_independent"])
            self.assertFalse(body["secrets_exposed"])
            self.assertEqual(body["last_error_code"], "TELEMETRY-DISABLED-001")

    def test_release_allows_telemetry_paths_in_gate(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_INSTALL_PROFILE": "release"}, clear=False):
            self.assertFalse(path_allowed_for_active_profile("/api/dev-dashboard/status"))
            self.assertTrue(path_allowed_for_active_profile("/api/rescue/telemetry/health"))
            self.assertTrue(path_allowed_for_active_profile("/api/rescue/telemetry/v1/ingest"))

    def test_ingest_disabled_on_release_returns_503_not_profile_block(self) -> None:
        with tempfile.TemporaryDirectory() as td, patch.dict(
            os.environ, self._client_env(td, enabled="0"), clear=False
        ):
            client = TestClient(fastapi_app, base_url="http://localhost")
            resp = client.post("/api/rescue/telemetry/v1/ingest", json=_minimal_envelope())
            self.assertEqual(resp.status_code, 503)
            self.assertEqual(resp.json().get("code"), "TELEMETRY-DISABLED-001")
            self.assertNotEqual(resp.json().get("code"), "PROFILE_ROUTE_BLOCKED")

    def test_ingest_enabled_ack_when_env_set(self) -> None:
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ, self._client_env(td), clear=False):
            envelope = _minimal_envelope()
            client = TestClient(fastapi_app, base_url="http://localhost")
            resp = client.post(
                "/api/rescue/telemetry/v1/ingest",
                json=envelope,
                headers={"X-Setuphelfer-Payload-Hash": envelope["payload_hash_sha256"]},
            )
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json()["status"], "acknowledged")
            self.assertTrue(resp.json()["hash_match"])


if __name__ == "__main__":
    unittest.main()
