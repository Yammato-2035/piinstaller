from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from deploy.runner_lab_acceptance_report_export import build_runner_lab_acceptance_report_export

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _acceptance_stub() -> dict:
    return {
        "acceptance_status": "lab_ready_candidate",
        "operator_decision_required": True,
        "runbook_outcomes": [
            {
                "runbook_id": "RUNBOOK_SUDOERS_RUNTIME_DRYRUN",
                "status": "pass",
                "evidence_status": "complete",
                "safety_status": "ok",
                "required_repeat": False,
                "notes": [],
            }
        ],
        "evidence_summary": {
            "total_files": 7,
            "valid_files": 7,
            "invalid_files": 0,
            "missing_runbooks": [],
            "pass_count": 7,
            "failed_count": 0,
            "repeat_required_count": 0,
            "evidence_complete_count": 7,
            "evidence_partial_count": 0,
            "evidence_missing_count": 0,
        },
        "blocking_findings": [],
        "residual_risks": [
            "LAB_RISK_FIRST_HARDWARE_SCOPE_LIMITED",
            "LAB_RISK_SINGLE_HOST_ONLY",
            "LAB_RISK_LIMITED_MEDIA_TYPES",
            "LAB_RISK_OPERATOR_DEPENDENT",
            "LAB_RISK_NOT_PRODUCTION_READY",
        ],
        "required_repeats": [],
        "warnings": [],
        "errors": [],
    }


class DeployRunnerLabAcceptanceReportExportV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.expected_files = [
            _REPO_ROOT / "docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT_DE.md",
            _REPO_ROOT / "docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT_EN.md",
            _REPO_ROOT / "docs/evidence/lab-acceptance/LAB_ACCEPTANCE_REPORT.json",
            _REPO_ROOT / "docs/runbooks/deploy-runner/reports/LAB_ACCEPTANCE_SUMMARY_DE.md",
            _REPO_ROOT / "docs/runbooks/deploy-runner/reports/LAB_ACCEPTANCE_SUMMARY_EN.md",
        ]
        for p in self.expected_files:
            p.parent.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        for p in self.expected_files:
            if p.exists():
                p.unlink()
            tmp = p.with_name(p.name + ".tmp")
            if tmp.exists():
                tmp.unlink()

    def test_expected_report_files_generated(self) -> None:
        out = build_runner_lab_acceptance_report_export(acceptance=_acceptance_stub())
        self.assertEqual(out["export_status"], "ok")
        for p in self.expected_files:
            self.assertTrue(p.exists())

    def test_json_report_is_valid_json_and_required_fields(self) -> None:
        build_runner_lab_acceptance_report_export(acceptance=_acceptance_stub())
        data = json.loads(self.expected_files[2].read_text(encoding="utf-8"))
        for key in [
            "report_id",
            "generated_at",
            "acceptance_status",
            "operator_decision_required",
            "runbook_outcomes",
            "evidence_summary",
            "blocking_findings",
            "residual_risks",
            "required_repeats",
            "warnings",
            "errors",
        ]:
            self.assertIn(key, data)

    def test_de_en_report_contains_acceptance_status(self) -> None:
        build_runner_lab_acceptance_report_export(acceptance=_acceptance_stub())
        self.assertIn("Acceptance Status", self.expected_files[0].read_text(encoding="utf-8"))
        self.assertIn("Acceptance Status", self.expected_files[1].read_text(encoding="utf-8"))

    def test_summary_contains_not_production_ready(self) -> None:
        build_runner_lab_acceptance_report_export(acceptance=_acceptance_stub())
        self.assertIn("not production-ready", self.expected_files[3].read_text(encoding="utf-8").lower())
        self.assertIn("not production-ready", self.expected_files[4].read_text(encoding="utf-8").lower())

    def test_residual_risks_visible(self) -> None:
        build_runner_lab_acceptance_report_export(acceptance=_acceptance_stub())
        text = self.expected_files[0].read_text(encoding="utf-8")
        self.assertIn("LAB_RISK_NOT_PRODUCTION_READY", text)

    def test_operator_decision_required_visible(self) -> None:
        build_runner_lab_acceptance_report_export(acceptance=_acceptance_stub())
        text = self.expected_files[0].read_text(encoding="utf-8")
        self.assertIn("Operator Decision Required", text)

    def test_traversal_path_blocked(self) -> None:
        out = build_runner_lab_acceptance_report_export(
            acceptance=_acceptance_stub(),
            target_files={"report_de": "../forbidden.md"},
        )
        self.assertEqual(out["export_status"], "blocked")
        self.assertTrue(any("traversal_path_forbidden" in e for e in out["errors"]))

    def test_symlink_path_blocked(self) -> None:
        with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
            tmp.write("x")
            external = tmp.name
        self.addCleanup(lambda: os.path.exists(external) and os.unlink(external))
        link = _REPO_ROOT / "docs/evidence/lab-acceptance/symlink-report.md"
        if link.exists() or link.is_symlink():
            link.unlink()
        link.symlink_to(external)
        self.addCleanup(lambda: (link.exists() or link.is_symlink()) and link.unlink())
        out = build_runner_lab_acceptance_report_export(
            acceptance=_acceptance_stub(),
            target_files={"report_de": "docs/evidence/lab-acceptance/symlink-report.md"},
        )
        self.assertEqual(out["export_status"], "blocked")
        self.assertTrue(any("symlink_path_forbidden" in e for e in out["errors"]))

    def test_atomic_write_no_tmp_leftover(self) -> None:
        build_runner_lab_acceptance_report_export(acceptance=_acceptance_stub())
        for p in self.expected_files:
            self.assertFalse(p.with_name(p.name + ".tmp").exists())

    def test_no_system_paths_written(self) -> None:
        out = build_runner_lab_acceptance_report_export(acceptance=_acceptance_stub())
        self.assertEqual(out["export_status"], "ok")
        for rel in out["generated_files"]:
            self.assertFalse(str(rel).startswith("/etc"))
            self.assertFalse(str(rel).startswith("/opt"))
            self.assertFalse(str(rel).startswith("/var/lib"))
            self.assertTrue(
                str(rel).startswith("docs/evidence/lab-acceptance/")
                or str(rel).startswith("docs/runbooks/deploy-runner/reports/")
            )

    def test_no_execute_apply_install_write_delete_route_except_export(self) -> None:
        routes = (_REPO_ROOT / "backend/deploy/routes.py").read_text(encoding="utf-8")
        self.assertIn("/runner/lab-readiness/acceptance/export", routes)
        self.assertNotIn("/runner/lab-readiness/acceptance/export/execute", routes)
        self.assertNotIn("/runner/lab-readiness/acceptance/export/apply", routes)
        self.assertNotIn("/runner/lab-readiness/acceptance/export/install", routes)
        self.assertNotIn("/runner/lab-readiness/acceptance/export/write", routes)
        self.assertNotIn("/runner/lab-readiness/acceptance/export/delete", routes)

    def test_no_forbidden_systemcalls(self) -> None:
        src = (_REPO_ROOT / "backend/deploy/runner_lab_acceptance_report_export.py").read_text(encoding="utf-8").lower()
        for token in ["subprocess", "os.system", "chmod(", "chown(", "systemctl", " dd ", "mkfs", "mount ", "umount"]:
            self.assertNotIn(token, src)


if __name__ == "__main__":
    unittest.main()
