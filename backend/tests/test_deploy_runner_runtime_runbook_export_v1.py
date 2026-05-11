"""Tests fuer Runtime Runbook Export Package."""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
_REPO = _BACKEND.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from deploy.runner_runtime_runbook_export import build_runner_runtime_runbook_export_package


class TestDeployRunnerRuntimeRunbookExportV1(unittest.TestCase):
    def test_expected_files_generated_under_allowed_paths(self):
        out = build_runner_runtime_runbook_export_package()
        self.assertEqual("ok", out["export_status"])
        generated = list(out["generated_files"])
        self.assertEqual(8, len(generated))
        for p in generated:
            self.assertTrue(p.startswith("docs/runbooks/deploy-runner/") or p.startswith("docs/evidence/templates/"))
            self.assertTrue((_REPO / p).exists())

    def test_master_runbook_contains_all_7_runbooks(self):
        build_runner_runtime_runbook_export_package()
        text = (_REPO / "docs" / "runbooks" / "deploy-runner" / "RUNTIME_RUNBOOK_MASTER_DE.md").read_text(encoding="utf-8")
        for rid in [
            "RUNBOOK_SUDOERS_RUNTIME_DRYRUN",
            "RUNBOOK_PRIVILEGED_RUNNER_VALIDATION_DRYRUN",
            "RUNBOOK_REAL_WRITE_HARDWARE_E2E",
            "RUNBOOK_FAILURE_INJECTION_HARDWARE_E2E",
            "RUNBOOK_DEVICE_REENUMERATION",
            "RUNBOOK_HOTPLUG_UNMOUNT_RACE",
            "RUNBOOK_ROLLBACK_RUNTIME",
        ]:
            self.assertIn(rid, text)

    def test_operator_checklist_contains_checkboxes(self):
        build_runner_runtime_runbook_export_package()
        text = (_REPO / "docs" / "runbooks" / "deploy-runner" / "OPERATOR_CHECKLIST_DE.md").read_text(encoding="utf-8")
        self.assertIn("- [ ]", text)

    def test_evidence_template_contains_core_sections(self):
        build_runner_runtime_runbook_export_package()
        text = (_REPO / "docs" / "evidence" / "templates" / "RUNNER_RUNTIME_RESULT_TEMPLATE.md").read_text(encoding="utf-8")
        self.assertIn("lsblk", text)
        self.assertIn("findmnt", text)
        self.assertIn("mount", text)
        self.assertIn("Audit JSONL", text)
        self.assertIn("Jobfile Hash", text)
        self.assertIn("Snapshot/Fingerprint", text)

    def test_result_schema_valid_json_and_required_fields(self):
        build_runner_runtime_runbook_export_package()
        text = (_REPO / "docs" / "evidence" / "templates" / "RUNNER_RUNTIME_RESULT_SCHEMA.json").read_text(encoding="utf-8")
        data = json.loads(text)
        req = set(data.get("required") or [])
        for key in [
            "runbook_id",
            "started_at",
            "completed_at",
            "operator",
            "host",
            "target_device",
            "pre_state",
            "post_state",
            "runner_result",
            "evidence",
            "pass_fail",
            "rollback_status",
        ]:
            self.assertIn(key, req)

    def test_acceptance_form_contains_decisions(self):
        build_runner_runtime_runbook_export_package()
        text = (_REPO / "docs" / "evidence" / "templates" / "RUNNER_RUNTIME_ACCEPTANCE_FORM_DE.md").read_text(encoding="utf-8")
        self.assertIn("lab_ready_candidate", text)
        self.assertIn("repeat_required", text)
        self.assertIn("blocked", text)

    def test_traversal_path_blocked(self):
        out = build_runner_runtime_runbook_export_package(target_files={"master_de": "../bad.md"})
        self.assertEqual("blocked", out["export_status"])

    def test_symlink_path_blocked(self):
        link = _REPO / "docs" / "runbooks" / "deploy-runner" / "LINK.md"
        target = _REPO / "docs" / "runbooks" / "deploy-runner" / "RUNTIME_RUNBOOK_MASTER_DE.md"
        if link.exists() or link.is_symlink():
            link.unlink()
        link.symlink_to(target)
        try:
            out = build_runner_runtime_runbook_export_package(target_files={"master_de": "docs/runbooks/deploy-runner/LINK.md"})
            self.assertEqual("blocked", out["export_status"])
        finally:
            if link.exists() or link.is_symlink():
                link.unlink()

    def test_atomic_write_no_tmp_leftover(self):
        build_runner_runtime_runbook_export_package()
        self.assertFalse((_REPO / "docs" / "runbooks" / "deploy-runner" / "RUNTIME_RUNBOOK_MASTER_DE.md.tmp").exists())

    def test_no_execute_apply_install_write_delete_route_except_export(self):
        try:
            from fastapi import FastAPI
        except ImportError:
            self.skipTest("fastapi nicht installiert")
        import deploy.routes as routes_mod

        app = FastAPI()
        app.include_router(routes_mod.router)
        paths = {getattr(r, "path", "") for r in app.routes}
        self.assertIn("/api/deploy/runner/runtime-runbook/export", paths)
        self.assertNotIn("/api/deploy/runner/runtime-runbook/execute", paths)
        self.assertNotIn("/api/deploy/runner/runtime-runbook/apply", paths)
        self.assertNotIn("/api/deploy/runner/runtime-runbook/install", paths)
        self.assertNotIn("/api/deploy/runner/runtime-runbook/write", paths)
        self.assertNotIn("/api/deploy/runner/runtime-runbook/delete", paths)

    def test_no_forbidden_systemcalls(self):
        src = (_BACKEND / "deploy" / "runner_runtime_runbook_export.py").read_text(encoding="utf-8").lower()
        forbidden_patterns = [
            r"\bsudo\b",
            r"\bvisudo\b",
            r"subprocess\.",
            r"os\.system\(",
            r"chmod\(",
            r"chown\(",
            r"\bsystemctl\b",
            r"\bdd\b",
            r"\bmkfs\b",
            r"mount\(",
            r"umount\(",
        ]
        for pat in forbidden_patterns:
            self.assertIsNone(re.search(pat, src), msg=pat)

