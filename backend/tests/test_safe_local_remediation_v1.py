"""Unit tests for allowlist-only safe local remediation (007 Phase 8)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from rescue.safe_local_remediation import (
    ALLOWED_ACTIONS,
    apply_remediation,
    plan_remediation,
)


class SafeLocalRemediationTests(unittest.TestCase):
    def test_allowlist_contains_expected_actions(self) -> None:
        for aid in (
            "retry_readonly_probe",
            "restart_setuphelfer_service",
            "kill_duplicate_setuphelfer_process",
            "remount_detect_only",
            "reinit_network",
            "clear_soft_rfkill",
            "activate_tui_fallback",
            "plan_next_boot_profile_params",
        ):
            self.assertIn(aid, ALLOWED_ACTIONS)

    def test_plan_allows_allowlisted(self) -> None:
        plan = plan_remediation(
            "reinit_network",
            reason="dhcp_timeout",
            before_state={"network": "down"},
        )
        self.assertTrue(plan["allowed"])
        self.assertEqual(plan["blockers"], [])
        self.assertEqual(plan["result"], "planned")

    def test_plan_refuses_forbidden(self) -> None:
        for aid in (
            "apt_install_nvidia",
            "dkms_install_module",
            "firmware_flash_nvme",
            "bios_update",
            "partition_write_nvme",
            "internal_disk_write",
            "shell_rm_rf",
            "not_a_real_action",
        ):
            plan = plan_remediation(aid, reason="x", before_state={})
            self.assertFalse(plan["allowed"], aid)
            self.assertIn("action_not_allowlisted", plan["blockers"])

    def test_apply_refused_does_not_call_executor(self) -> None:
        called = {"n": 0}

        def executor(action_id, before_state):
            called["n"] += 1
            return {"ok": True}

        out = apply_remediation(
            "apt_install_something",
            reason="nope",
            before_state={"x": 1},
            executor=executor,
        )
        self.assertEqual(called["n"], 0)
        self.assertEqual(out["result"], "refused")
        self.assertFalse(out["allowed"])
        self.assertEqual(out["before_state"], {"x": 1})
        self.assertIn("action_id", out)
        self.assertIn("rollback", out)

    def test_apply_calls_executor_when_allowed(self) -> None:
        def executor(action_id, before_state):
            self.assertEqual(action_id, "clear_soft_rfkill")
            return {**dict(before_state), "rfkill": "unblocked"}

        out = apply_remediation(
            "clear_soft_rfkill",
            reason="wlan_soft_blocked",
            before_state={"rfkill": "soft"},
            executor=executor,
        )
        self.assertTrue(out["allowed"])
        self.assertEqual(out["result"], "applied")
        self.assertEqual(out["after_state"]["rfkill"], "unblocked")
        self.assertEqual(out["reason"], "wlan_soft_blocked")
        self.assertIn("action", out)
        self.assertIn("rollback", out)

    def test_apply_without_executor_is_planned_only(self) -> None:
        out = apply_remediation(
            "activate_tui_fallback",
            reason="xorg_failed",
            before_state={"ui": "xorg"},
            executor=None,
        )
        self.assertEqual(out["result"], "planned_only")
        self.assertTrue(out["allowed"])

    def test_missing_reason_blocks(self) -> None:
        plan = plan_remediation("retry_readonly_probe", reason="", before_state={})
        self.assertFalse(plan["allowed"])
        self.assertIn("missing_reason", plan["blockers"])


if __name__ == "__main__":
    unittest.main()
