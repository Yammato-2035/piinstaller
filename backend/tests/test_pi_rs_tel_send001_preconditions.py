"""PI-RS-TEL-SEND-001 precondition gate tests."""

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
from core.rescue_stick_cloud_lab_send import evaluate_rescue_stick_lab_preconditions


def _ready_config(token_file: str) -> RescueStickLabSendConfig:
    return RescueStickLabSendConfig(
        lab_send_enabled=True,
        operator_approval=OPERATOR_APPROVAL_EXPLICIT,
        consent_status=CONSENT_STATUS_GRANTED_LAB,
        token_file=token_file,
        stick_version="1.9.19.5",
    )


class TelSend001PreconditionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.token_path = Path(self._tmpdir.name) / "token"
        self.token_path.write_text("test-lab-token-only\n", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_blocked_without_health_ok(self) -> None:
        result = evaluate_rescue_stick_lab_preconditions(
            _ready_config(str(self.token_path)),
            health_check=lambda _url, _timeout: "health_not_ok",
        )
        self.assertEqual(result.send_status, RescueStickLabSendStatus.BLOCKED_HEALTH_NOT_OK)

    def test_blocked_without_auth(self) -> None:
        cfg = _ready_config("/nonexistent/token-file")
        result = evaluate_rescue_stick_lab_preconditions(
            cfg,
            health_check=lambda _url, _timeout: "health_ok",
        )
        self.assertEqual(result.send_status, RescueStickLabSendStatus.BLOCKED_MISSING_AUTH)

    def test_blocked_without_consent(self) -> None:
        cfg = _ready_config(str(self.token_path))
        cfg = RescueStickLabSendConfig(
            lab_send_enabled=cfg.lab_send_enabled,
            operator_approval=cfg.operator_approval,
            consent_status="denied",
            ingest_url=cfg.ingest_url,
            token_file=cfg.token_file,
        )
        result = evaluate_rescue_stick_lab_preconditions(
            cfg,
            health_check=lambda _url, _timeout: "health_ok",
        )
        self.assertEqual(result.send_status, RescueStickLabSendStatus.BLOCKED_MISSING_CONSENT)

    def test_blocked_without_operator_approval(self) -> None:
        cfg = _ready_config(str(self.token_path))
        cfg = RescueStickLabSendConfig(
            lab_send_enabled=cfg.lab_send_enabled,
            operator_approval="implicit",
            consent_status=cfg.consent_status,
            ingest_url=cfg.ingest_url,
            token_file=cfg.token_file,
        )
        result = evaluate_rescue_stick_lab_preconditions(
            cfg,
            health_check=lambda _url, _timeout: "health_ok",
        )
        self.assertEqual(result.send_status, RescueStickLabSendStatus.BLOCKED_MISSING_OPERATOR_APPROVAL)

    def test_blocked_without_lab_send_flag(self) -> None:
        cfg = _ready_config(str(self.token_path))
        cfg = RescueStickLabSendConfig(
            lab_send_enabled=False,
            operator_approval=cfg.operator_approval,
            consent_status=cfg.consent_status,
            ingest_url=cfg.ingest_url,
            token_file=cfg.token_file,
        )
        result = evaluate_rescue_stick_lab_preconditions(
            cfg,
            health_check=lambda _url, _timeout: "health_ok",
        )
        self.assertEqual(result.send_status, RescueStickLabSendStatus.BLOCKED_LAB_SEND_DISABLED)


if __name__ == "__main__":
    unittest.main()
