"""PI-RS-TEL-SEND-001 preview tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.rescue_stick_cloud_lab_models import (
    CONSENT_STATUS_GRANTED_LAB,
    OPERATOR_APPROVAL_EXPLICIT,
    RescueStickLabSendConfig,
    RescueStickLabSendStatus,
)
from core.rescue_stick_cloud_lab_send import preview_rescue_stick_lab_send


class TelSend001PreviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.token_path = Path(self._tmpdir.name) / "token"
        self.token_path.write_text("preview-token\n", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_preview_does_not_execute_send(self) -> None:
        config = RescueStickLabSendConfig(
            lab_send_enabled=True,
            operator_approval=OPERATOR_APPROVAL_EXPLICIT,
            consent_status=CONSENT_STATUS_GRANTED_LAB,
            token_file=str(self.token_path),
            stick_version="1.9.19.5",
        )
        result = preview_rescue_stick_lab_send(
            config,
            health_check=lambda _url, _timeout: "health_ok",
        )
        self.assertEqual(result.send_status, RescueStickLabSendStatus.DRY_RUN_READY)
        self.assertFalse(result.real_send_executed)
        self.assertEqual(result.source, "rescue_stick")
        self.assertTrue(result.auth_present)


if __name__ == "__main__":
    unittest.main()
