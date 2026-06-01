"""Security model tests for rescue remote control phase 1."""

from __future__ import annotations

import unittest

from rescue_remote.service import (
    ALLOWLISTED_RUNBOOKS,
    FORBIDDEN_RUNBOOK_IDS,
    assert_runbook_allowed,
    redact_text,
    rescue_remote_enabled,
)
from rescue_remote.service import RescueRemoteError


class RescueRemoteSecurityModelTests(unittest.TestCase):
    def test_forbidden_runbooks_blocked(self) -> None:
        for rid in ("shell", "dd", "write_usb", "arbitrary_command"):
            with self.assertRaises(RescueRemoteError) as ctx:
                assert_runbook_allowed(rid, "read_only")
            self.assertEqual(ctx.exception.code, "RESCUE_REMOTE_JOB_BLOCKED")

    def test_allowlisted_read_only(self) -> None:
        meta = assert_runbook_allowed("collect_boot_logs", "read_only")
        self.assertEqual(meta["allowed_mode"], "read_only")

    def test_controlled_write_mode_blocked(self) -> None:
        with self.assertRaises(RescueRemoteError):
            assert_runbook_allowed("collect_boot_logs", "controlled_write")

    def test_no_shell_in_allowlist(self) -> None:
        self.assertNotIn("shell", ALLOWLISTED_RUNBOOKS)
        self.assertIn("shell", FORBIDDEN_RUNBOOK_IDS)

    def test_redact_tokens(self) -> None:
        text, warnings = redact_text("password=SuperSecret123")
        self.assertIn("[REDACTED]", text)
        self.assertTrue(warnings)

    def test_enabled_in_dev(self) -> None:
        import os
        from unittest.mock import patch

        with patch.dict(os.environ, {"SETUPHELFER_RESCUE_REMOTE_ENABLED": "true"}, clear=False):
            self.assertTrue(rescue_remote_enabled())


if __name__ == "__main__":
    unittest.main()
