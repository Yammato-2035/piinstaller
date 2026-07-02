"""Mock server integration smoke test."""

from __future__ import annotations

import json
import threading
import unittest
import urllib.request
from http.server import HTTPServer

from dev.telemetry_mock_server_v2 import TelemetryMockHandler, MOCK_PORT
from core.rescue_telemetry_client_contract_v2 import build_telemetry_payload_v2
from core.rescue_telemetry_upload_v1 import upload_telemetry_payload_v1


class TelemetryMockIntegrationV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._server = HTTPServer(("127.0.0.1", MOCK_PORT), TelemetryMockHandler)
        cls._thread = threading.Thread(target=cls._server.serve_forever, daemon=True)
        cls._thread.start()
        with urllib.request.urlopen(f"http://127.0.0.1:{MOCK_PORT}/health", timeout=3) as resp:
            cls._health_ok = resp.status == 200

    @classmethod
    def tearDownClass(cls) -> None:
        cls._server.shutdown()

    def test_health_reachable(self) -> None:
        self.assertTrue(self._health_ok)

    def test_mock_upload_dry_run_path(self) -> None:
        payload = build_telemetry_payload_v2(
            rescue_version="1.9.17.1",
            build_id="mock",
            boot_session_id="boot",
            stick_id="stick-mock",
            stick_type="mock",
            device_public_key_id="key",
            attestation_mode="mock",
            system_assessment={"issue_codes": []},
        )
        result = upload_telemetry_payload_v1(payload, mode="mock_server", stick_verified=True)
        self.assertIn(result["status"], {"dry_run_ok", "mock_response", "accepted"})


if __name__ == "__main__":
    unittest.main()
