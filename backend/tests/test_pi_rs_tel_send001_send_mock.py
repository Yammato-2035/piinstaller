"""PI-RS-TEL-SEND-001 mock send classification tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.rescue_stick_cloud_lab_models import (
    CONSENT_STATUS_GRANTED_LAB,
    OPERATOR_APPROVAL_EXPLICIT,
    RescueStickLabSendConfig,
    RescueStickLabSendStatus,
)
from core.rescue_stick_cloud_lab_send import execute_rescue_stick_lab_send


class TelSend001SendMockTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.token_path = Path(self._tmpdir.name) / "token"
        self.token_path.write_text("mock-send-token\n", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _config(self) -> RescueStickLabSendConfig:
        return RescueStickLabSendConfig(
            lab_send_enabled=True,
            operator_approval=OPERATOR_APPROVAL_EXPLICIT,
            consent_status=CONSENT_STATUS_GRANTED_LAB,
            token_file=str(self.token_path),
            stick_version="1.9.19.5",
        )

    def test_mock_accepted(self) -> None:
        def transport(_url: str, _body: bytes, _headers: dict[str, str], _timeout: int) -> tuple[int, str, dict[str, str]]:
            return 200, json.dumps({"accepted": True, "status": "accepted", "request_id": "req-mock-001"}), {}

        result = execute_rescue_stick_lab_send(
            self._config(),
            health_check=lambda _url, _timeout: "health_ok",
            http_transport=transport,
        )
        self.assertEqual(result.send_status, RescueStickLabSendStatus.LAB_SEND_ACCEPTED)
        self.assertEqual(result.response_classification, "lab_send_accepted")
        self.assertEqual(result.request_id, "req-mock-001")

    def test_mock_rejected_auth(self) -> None:
        def transport(_url: str, _body: bytes, _headers: dict[str, str], _timeout: int) -> tuple[int, str, dict[str, str]]:
            return 403, json.dumps({"accepted": False, "status": "rejected_auth"}), {}

        result = execute_rescue_stick_lab_send(
            self._config(),
            health_check=lambda _url, _timeout: "health_ok",
            http_transport=transport,
        )
        self.assertEqual(result.send_status, RescueStickLabSendStatus.LAB_SEND_REJECTED)
        self.assertEqual(result.response_classification, "lab_send_rejected_auth")

    def test_mock_failed_transport(self) -> None:
        def transport(_url: str, _body: bytes, _headers: dict[str, str], _timeout: int) -> tuple[int, str, dict[str, str]]:
            return 0, "connection refused", {}

        result = execute_rescue_stick_lab_send(
            self._config(),
            health_check=lambda _url, _timeout: "health_ok",
            http_transport=transport,
        )
        self.assertEqual(result.send_status, RescueStickLabSendStatus.LAB_SEND_FAILED)


if __name__ == "__main__":
    unittest.main()
