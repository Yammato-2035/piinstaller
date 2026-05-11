"""Tests fuer Runtime Execution Runbook Bundle."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from deploy.runner_runtime_runbook_bundle import build_runner_runtime_runbook_bundle


class TestDeployRunnerRuntimeRunbookBundleV1(unittest.TestCase):
    def test_all_7_runbooks_present(self):
        out = build_runner_runtime_runbook_bundle()
        seq = list(out["runbook_sequence"])
        self.assertEqual(7, len(seq))

    def test_runbook_order_exact(self):
        out = build_runner_runtime_runbook_bundle()
        ids = [str(x.get("runbook_id") or "") for x in out["runbook_sequence"]]
        self.assertEqual(
            [
                "RUNBOOK_SUDOERS_RUNTIME_DRYRUN",
                "RUNBOOK_PRIVILEGED_RUNNER_VALIDATION_DRYRUN",
                "RUNBOOK_REAL_WRITE_HARDWARE_E2E",
                "RUNBOOK_FAILURE_INJECTION_HARDWARE_E2E",
                "RUNBOOK_DEVICE_REENUMERATION",
                "RUNBOOK_HOTPLUG_UNMOUNT_RACE",
                "RUNBOOK_ROLLBACK_RUNTIME",
            ],
            ids,
        )

    def test_all_runbooks_auto_allowed_false(self):
        out = build_runner_runtime_runbook_bundle()
        for item in out["runbook_sequence"]:
            self.assertFalse(bool(item.get("auto_allowed")))

    def test_all_runbooks_manual_operator_required_true(self):
        out = build_runner_runtime_runbook_bundle()
        for item in out["runbook_sequence"]:
            self.assertTrue(bool(item.get("manual_operator_required")))

    def test_global_preconditions_contain_backup_media_local_access(self):
        out = build_runner_runtime_runbook_bundle()
        codes = {str((x or {}).get("code") or "") for x in list(out["global_preconditions"])}
        self.assertIn("GLOBAL_PRECONDITION_FULL_BACKUP", codes)
        self.assertIn("GLOBAL_PRECONDITION_SINGLE_DISPOSABLE_MEDIA", codes)
        self.assertIn("GLOBAL_PRECONDITION_LOCAL_HOST_ACCESS", codes)

    def test_global_stop_conditions_contain_operator_systemdisk_verify(self):
        out = build_runner_runtime_runbook_bundle()
        stops = list(out["global_stop_conditions"])
        self.assertIn("operator_unsure", stops)
        self.assertIn("systemdisk_as_target", stops)
        self.assertIn("verify_mismatch", stops)

    def test_global_evidence_contains_core_items(self):
        out = build_runner_runtime_runbook_bundle()
        ev = list(out["global_evidence_requirements"])
        self.assertIn("lsblk_before_after", ev)
        self.assertIn("findmnt_before_after", ev)
        self.assertIn("mount_before_after", ev)
        self.assertIn("audit_jsonl", ev)
        self.assertIn("jobfile_hash", ev)
        self.assertIn("snapshot_fingerprint", ev)

    def test_operator_checklist_must_ack_true(self):
        out = build_runner_runtime_runbook_bundle()
        for item in out["operator_checklist"]:
            self.assertTrue(bool(item.get("must_acknowledge")))

    def test_per_runbook_has_pass_fail_criteria(self):
        out = build_runner_runtime_runbook_bundle()
        for rb in out["per_runbook"]:
            self.assertTrue(bool(rb.get("pass_criteria")))
            self.assertTrue(bool(rb.get("fail_criteria")))

    def test_no_execute_apply_install_write_delete_route_present(self):
        try:
            from fastapi import FastAPI
        except ImportError:
            self.skipTest("fastapi nicht installiert")
        import deploy.routes as routes_mod

        app = FastAPI()
        app.include_router(routes_mod.router)
        paths = {getattr(r, "path", "") for r in app.routes}
        self.assertIn("/api/deploy/runner/runtime-runbook/bundle", paths)
        self.assertNotIn("/api/deploy/runner/runtime-runbook/execute", paths)
        self.assertNotIn("/api/deploy/runner/runtime-runbook/apply", paths)
        self.assertNotIn("/api/deploy/runner/runtime-runbook/install", paths)
        self.assertNotIn("/api/deploy/runner/runtime-runbook/write", paths)
        self.assertNotIn("/api/deploy/runner/runtime-runbook/delete", paths)

    def test_no_forbidden_systemcalls(self):
        src = (_BACKEND / "deploy" / "runner_runtime_runbook_bundle.py").read_text(encoding="utf-8").lower()
        forbidden_patterns = [
            r"\bsudo\b",
            r"\bvisudo\b",
            r"subprocess\.",
            r"os\.system\(",
            r"chmod\(",
            r"chown\(",
            r"mkdir\(",
            r"\brm\b",
            r"\bsystemctl\b",
            r"\bdd\b",
            r"\bmkfs\b",
            r"mount\(",
            r"umount\(",
        ]
        for pat in forbidden_patterns:
            self.assertIsNone(re.search(pat, src), msg=pat)

