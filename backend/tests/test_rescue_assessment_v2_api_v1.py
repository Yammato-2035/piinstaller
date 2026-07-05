"""Rescue Assessment V2 API route tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

try:
    from fastapi.testclient import TestClient

    from app import app

    _HAS_TC = True
except Exception:
    TestClient = None  # type: ignore[misc, assignment]
    app = None  # type: ignore[misc, assignment]
    _HAS_TC = False


@unittest.skipUnless(_HAS_TC, "fastapi/testclient not available")
class RescueAssessmentV2ApiTests(unittest.TestCase):
    def test_network_connectivity_route(self) -> None:
        client = TestClient(app)
        with patch(
            "api.routes.rescue_assessment_v2.build_network_connectivity_v2",
            return_value={"schema_version": "network-connectivity.v2", "issue_codes": ["dns_ok"]},
        ):
            resp = client.get("/api/rescue/network-connectivity-v2")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["schema_version"], "network-connectivity.v2")

    def test_telemetry_connectivity_route(self) -> None:
        client = TestClient(app)
        with patch(
            "api.routes.rescue_assessment_v2.build_telemetry_connectivity_v1",
            return_value={"schema_version": "telemetry-connectivity.v1", "issue_codes": []},
        ):
            resp = client.get("/api/rescue/telemetry-connectivity-v1")
        self.assertEqual(resp.status_code, 200)

    def test_telemetry_upload_dry_run(self) -> None:
        client = TestClient(app)
        payload = {
            "schema_version": "telemetry.rescue.beta.v2",
            "event_id": "00000000-0000-4000-8000-000000000001",
            "created_at": "2026-07-02T12:00:00Z",
            "rescue_version": "1.9.17.1",
            "build_id": "b",
            "boot_session_id": "s",
            "stick": {
                "stick_id": "stick-mock",
                "stick_type": "mock",
                "device_public_key_id": "k",
                "attestation_mode": "mock",
            },
            "beta": {"account_status": "unknown", "agreement_status": "unknown", "upload_allowed": False},
            "machine": {"machine_fingerprint": "fp", "approval_status": "unknown"},
            "system_assessment": {},
            "privacy": {
                "redaction_version": "v2",
                "contains_mac": False,
                "contains_ip": False,
                "contains_email": False,
                "contains_serial_plaintext": False,
                "contains_file_list": False,
                "contains_user_files": False,
                "contains_secrets": False,
            },
        }
        resp = client.post(
            "/api/rescue/telemetry/upload-v1",
            json={"payload": payload, "mode": "dry_run_local"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "dry_run_ok")

    def test_master_bundle_route(self) -> None:
        client = TestClient(app)
        with patch(
            "api.routes.rescue_assessment_v2.build_master_assessment_bundle_v1",
            return_value={"schema_version": "rescue.master_assessment_bundle.v1"},
        ):
            resp = client.get("/api/rescue/master-assessment-bundle-v1")
        self.assertEqual(resp.status_code, 200)


if __name__ == "__main__":
    unittest.main()
