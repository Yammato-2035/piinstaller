from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from deploy.runner_manual_runtime_result_template import create_manual_runtime_result_template

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _precheck(status: str = "ready_for_manual_runtime", runbook: str = "RUNBOOK_SUDOERS_RUNTIME_DRYRUN", path: str | None = None) -> dict:
    result_path = path or f"docs/evidence/runtime-results/{runbook}.json"
    return {
        "precheck_status": status,
        "selected_runbook": runbook,
        "evidence_plan": [{"code": "EVIDENCE_RESULT_FILE_PATH", "value": result_path, "auto_allowed": False}],
    }


class DeployRunnerManualRuntimeResultTemplateV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.allowed_root = _REPO_ROOT / "docs/evidence/runtime-results"
        self.allowed_root.mkdir(parents=True, exist_ok=True)
        self.cleanup_paths: list[Path] = []

    def tearDown(self) -> None:
        for p in self.cleanup_paths:
            if p.exists() or p.is_symlink():
                p.unlink()
            tmp = p.with_name(p.name + ".tmp")
            if tmp.exists():
                tmp.unlink()

    def test_ready_precheck_creates_template(self) -> None:
        runbook = "RUNBOOK_SUDOERS_RUNTIME_DRYRUN"
        p = self.allowed_root / f"{runbook}.json"
        self.cleanup_paths.append(p)
        out = create_manual_runtime_result_template(precheck=_precheck(runbook=runbook))
        self.assertEqual(out["template_status"], "created")
        self.assertTrue(p.exists())

    def test_review_required_precheck_creates_with_warning(self) -> None:
        runbook = "RUNBOOK_SUDOERS_RUNTIME_DRYRUN"
        p = self.allowed_root / "review.json"
        self.cleanup_paths.append(p)
        out = create_manual_runtime_result_template(precheck=_precheck(status="review_required", runbook=runbook, path="docs/evidence/runtime-results/review.json"))
        self.assertEqual(out["template_status"], "review_required")
        self.assertIn("precheck_review_required", out["warnings"])

    def test_blocked_precheck_blocks(self) -> None:
        out = create_manual_runtime_result_template(precheck=_precheck(status="blocked"))
        self.assertEqual(out["template_status"], "blocked")

    def test_unknown_runbook_blocks(self) -> None:
        out = create_manual_runtime_result_template(precheck=_precheck(runbook="UNKNOWN_RUNBOOK"))
        self.assertEqual(out["template_status"], "blocked")

    def test_path_outside_allowed_root_blocks(self) -> None:
        out = create_manual_runtime_result_template(precheck=_precheck(path="docs/evidence/other/out.json"))
        self.assertEqual(out["template_status"], "blocked")

    def test_traversal_path_blocks(self) -> None:
        out = create_manual_runtime_result_template(precheck=_precheck(path="docs/evidence/runtime-results/../evil.json"))
        self.assertEqual(out["template_status"], "blocked")

    def test_symlink_path_blocks(self) -> None:
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tmp:
            tmp.write("{}")
            external = tmp.name
        self.addCleanup(lambda: os.path.exists(external) and os.unlink(external))
        symlink_path = self.allowed_root / "symlink.json"
        symlink_path.symlink_to(external)
        self.cleanup_paths.append(symlink_path)
        out = create_manual_runtime_result_template(precheck=_precheck(path="docs/evidence/runtime-results/symlink.json"))
        self.assertEqual(out["template_status"], "blocked")

    def test_existing_file_without_explicit_overwrite_blocks(self) -> None:
        p = self.allowed_root / "exists.json"
        p.write_text("{}", encoding="utf-8")
        self.cleanup_paths.append(p)
        out = create_manual_runtime_result_template(precheck=_precheck(path="docs/evidence/runtime-results/exists.json"), explicit_overwrite=False)
        self.assertEqual(out["template_status"], "blocked")

    def test_explicit_overwrite_true_allows_overwrite(self) -> None:
        p = self.allowed_root / "overwrite.json"
        p.write_text("{}", encoding="utf-8")
        self.cleanup_paths.append(p)
        out = create_manual_runtime_result_template(precheck=_precheck(path="docs/evidence/runtime-results/overwrite.json"), explicit_overwrite=True)
        self.assertIn(out["template_status"], {"created", "review_required"})
        data = json.loads(p.read_text(encoding="utf-8"))
        self.assertIn("runbook_id", data)

    def test_template_contains_required_fields(self) -> None:
        p = self.allowed_root / "required.json"
        self.cleanup_paths.append(p)
        create_manual_runtime_result_template(precheck=_precheck(path="docs/evidence/runtime-results/required.json"))
        data = json.loads(p.read_text(encoding="utf-8"))
        for key in ["runbook_id", "started_at", "completed_at", "operator", "host", "target_device", "pre_state", "post_state", "runner_result", "evidence", "pass_fail", "rollback_status"]:
            self.assertIn(key, data)

    def test_dryrun_template_has_sha_fields_empty_or_null(self) -> None:
        p = self.allowed_root / "dryrun.json"
        self.cleanup_paths.append(p)
        create_manual_runtime_result_template(precheck=_precheck(path="docs/evidence/runtime-results/dryrun.json", runbook="RUNBOOK_SUDOERS_RUNTIME_DRYRUN"))
        data = json.loads(p.read_text(encoding="utf-8"))
        ev = data["evidence"]
        self.assertIsNone(ev["bytes_written"])
        self.assertEqual(ev["expected_sha256"], "")
        self.assertEqual(ev["actual_sha256"], "")
        self.assertEqual(ev["verify_status"], "")

    def test_no_execute_apply_install_write_delete_release_route(self) -> None:
        routes = (_REPO_ROOT / "backend/deploy/routes.py").read_text(encoding="utf-8")
        self.assertIn("/runner/manual-runtime/result-template", routes)
        for forbidden in [
            "/runner/manual-runtime/result-template/execute",
            "/runner/manual-runtime/result-template/apply",
            "/runner/manual-runtime/result-template/install",
            "/runner/manual-runtime/result-template/write",
            "/runner/manual-runtime/result-template/delete",
            "/runner/manual-runtime/result-template/release",
        ]:
            self.assertNotIn(forbidden, routes)

    def test_no_forbidden_systemcalls(self) -> None:
        src = (_REPO_ROOT / "backend/deploy/runner_manual_runtime_result_template.py").read_text(encoding="utf-8").lower()
        for token in ["subprocess", "os.system", "chmod(", "chown(", "systemctl", " dd ", "mkfs", "mount ", "umount"]:
            self.assertNotIn(token, src)


if __name__ == "__main__":
    unittest.main()
