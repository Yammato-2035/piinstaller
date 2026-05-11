from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from deploy.runner_manual_runtime_result_validator_dryrun_from_handoff import run_manual_runtime_result_validator_dryrun_from_handoff

_REPO_ROOT = Path(__file__).resolve().parents[2]

_SEQUENCE = [
    "RUNBOOK_SUDOERS_RUNTIME_DRYRUN",
    "RUNBOOK_PRIVILEGED_RUNNER_VALIDATION_DRYRUN",
    "RUNBOOK_REAL_WRITE_HARDWARE_E2E",
    "RUNBOOK_FAILURE_INJECTION_HARDWARE_E2E",
    "RUNBOOK_DEVICE_REENUMERATION",
    "RUNBOOK_HOTPLUG_UNMOUNT_RACE",
    "RUNBOOK_ROLLBACK_RUNTIME",
]

_MANIFEST_REL = "docs/evidence/runtime-results/handoff/validator_handoff_manifest.json"
_REPORT_REL = "docs/evidence/runtime-results/handoff/validator_dryrun_report.json"


def _valid_payload(runbook_id: str, pass_fail: str = "pass") -> dict:
    return {
        "runbook_id": runbook_id,
        "started_at": "2026-05-08T10:00:00Z",
        "completed_at": "2026-05-08T10:10:00Z",
        "operator": "op",
        "host": "lab-host",
        "target_device": "/dev/sdx",
        "pre_state": {"ok": True},
        "post_state": {"ok": True},
        "runner_result": {"status": "ok"},
        "evidence": {
            "lsblk_before_after": {"before": "a", "after": "b"},
            "findmnt_before_after": {"before": "a", "after": "b"},
            "mount_before_after": {"before": "a", "after": "b"},
            "runner_stdout_json": {"ok": True},
            "audit_jsonl": [{"line": 1}],
            "jobfile_hash": "abc",
            "snapshot_fingerprint": {"before": "f1", "after": "f2"},
            "bytes_written": 1,
            "expected_sha256": "e",
            "actual_sha256": "e",
            "verify_status": "match",
        },
        "pass_fail": pass_fail,
        "rollback_status": "ok",
    }


class DeployRunnerManualRuntimeResultValidatorDryrunFromHandoffV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = _REPO_ROOT / "docs/evidence/runtime-results"
        self.handoff = self.root / "handoff"
        self.root.mkdir(parents=True, exist_ok=True)
        self.handoff.mkdir(parents=True, exist_ok=True)
        self.manifest = self.handoff / "validator_handoff_manifest.json"
        self.report = self.handoff / "validator_dryrun_report.json"
        self.cleanup_paths: list[Path] = []

    def tearDown(self) -> None:
        for p in self.cleanup_paths:
            if p.exists() or p.is_symlink():
                p.unlink()
        if self.report.exists():
            self.report.unlink()
        if self.manifest.exists():
            self.manifest.unlink()
        for tmp in self.handoff.glob("*.tmp"):
            if tmp.exists():
                tmp.unlink()

    def _write_result(self, name: str, payload: dict) -> str:
        p = self.root / name
        p.write_text(json.dumps(payload), encoding="utf-8")
        self.cleanup_paths.append(p)
        return str(p.relative_to(_REPO_ROOT))

    def _write_manifest(self, vif: list[str]) -> None:
        body = {
            "handoff_schema_version": 1,
            "validator_input_files": vif,
        }
        self.manifest.write_text(json.dumps(body), encoding="utf-8")

    def _seven_valid_paths(self) -> list[str]:
        paths: list[str] = []
        for i, rb in enumerate(_SEQUENCE):
            paths.append(self._write_result(f"dr{i}.json", _valid_payload(rb)))
        return paths

    def test_valid_manifest_runs_validator_dryrun(self) -> None:
        paths = self._seven_valid_paths()
        self._write_manifest(paths)
        out = run_manual_runtime_result_validator_dryrun_from_handoff(handoff_manifest_path=_MANIFEST_REL, explicit_overwrite=False)
        self.assertEqual(out["dryrun_status"], "ok")
        self.assertEqual(out["dryrun_report_path"], _REPORT_REL)
        self.assertTrue(self.report.is_file())
        rep = json.loads(self.report.read_text(encoding="utf-8"))
        self.assertEqual(rep["dryrun_status"], "ok")
        self.assertIn("validator_result", rep)

    def test_missing_manifest_blocked(self) -> None:
        if self.manifest.exists():
            self.manifest.unlink()
        out = run_manual_runtime_result_validator_dryrun_from_handoff(handoff_manifest_path=_MANIFEST_REL)
        self.assertEqual(out["dryrun_status"], "blocked")
        self.assertIn("DRYRUN_MANIFEST_MISSING", out["blocked_reasons"])

    def test_manifest_outside_handoff_blocked(self) -> None:
        leak = self.root / "leak_manifest.json"
        leak.write_text(json.dumps({"validator_input_files": []}), encoding="utf-8")
        self.cleanup_paths.append(leak)
        rel = str(leak.relative_to(_REPO_ROOT))
        out = run_manual_runtime_result_validator_dryrun_from_handoff(handoff_manifest_path=rel)
        self.assertEqual(out["dryrun_status"], "blocked")
        self.assertIn("DRYRUN_MANIFEST_OUTSIDE_HANDOFF", out["blocked_reasons"])

    def test_traversal_blocked(self) -> None:
        out = run_manual_runtime_result_validator_dryrun_from_handoff(
            handoff_manifest_path="docs/evidence/runtime-results/handoff/../handoff/x.json",
        )
        self.assertEqual(out["dryrun_status"], "blocked")

    def test_symlink_manifest_blocked(self) -> None:
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tmp:
            tmp.write("{}")
            ext = tmp.name
        self.addCleanup(lambda: os.path.exists(ext) and os.unlink(ext))
        link = self.handoff / "sym_manifest.json"
        link.symlink_to(ext)
        self.cleanup_paths.append(link)
        rel = str(link.relative_to(_REPO_ROOT))
        out = run_manual_runtime_result_validator_dryrun_from_handoff(handoff_manifest_path=rel)
        self.assertEqual(out["dryrun_status"], "blocked")
        self.assertIn("DRYRUN_SYMLINK_BLOCKED", out["blocked_reasons"])

    def test_wrong_file_count_blocked(self) -> None:
        paths = self._seven_valid_paths()[:6]
        self._write_manifest(paths)
        out = run_manual_runtime_result_validator_dryrun_from_handoff(handoff_manifest_path=_MANIFEST_REL)
        self.assertEqual(out["dryrun_status"], "blocked")
        self.assertIn("DRYRUN_VALIDATOR_INPUT_FILES_COUNT_NOT_SEVEN", out["blocked_reasons"])

    def test_missing_result_file_blocked(self) -> None:
        paths = self._seven_valid_paths()
        self._write_manifest(paths)
        Path(self.root / Path(paths[2]).name).unlink()
        out = run_manual_runtime_result_validator_dryrun_from_handoff(handoff_manifest_path=_MANIFEST_REL)
        self.assertEqual(out["dryrun_status"], "blocked")
        self.assertIn("DRYRUN_RESULT_FILE_MISSING", out["blocked_reasons"])

    def test_result_under_handoff_blocked(self) -> None:
        bad = self.handoff / "bad_result.json"
        bad.write_text(json.dumps(_valid_payload(_SEQUENCE[0])), encoding="utf-8")
        self.cleanup_paths.append(bad)
        rel_bad = str(bad.relative_to(_REPO_ROOT))
        paths = [rel_bad] + self._seven_valid_paths()[1:]
        self._write_manifest(paths)
        out = run_manual_runtime_result_validator_dryrun_from_handoff(handoff_manifest_path=_MANIFEST_REL)
        self.assertEqual(out["dryrun_status"], "blocked")
        self.assertIn("DRYRUN_RESULT_FILE_UNDER_HANDOFF_FORBIDDEN", out["blocked_reasons"])

    def test_existing_report_blocks_without_overwrite(self) -> None:
        paths = self._seven_valid_paths()
        self._write_manifest(paths)
        first = run_manual_runtime_result_validator_dryrun_from_handoff(handoff_manifest_path=_MANIFEST_REL)
        self.assertEqual(first["dryrun_status"], "ok")
        second = run_manual_runtime_result_validator_dryrun_from_handoff(handoff_manifest_path=_MANIFEST_REL, explicit_overwrite=False)
        self.assertEqual(second["dryrun_status"], "blocked")
        self.assertIn("DRYRUN_REPORT_EXISTS_NO_OVERWRITE", second["blocked_reasons"])

    def test_explicit_overwrite_rewrites_report(self) -> None:
        paths = self._seven_valid_paths()
        self._write_manifest(paths)
        first = run_manual_runtime_result_validator_dryrun_from_handoff(handoff_manifest_path=_MANIFEST_REL)
        self.assertEqual(first["dryrun_status"], "ok")
        second = run_manual_runtime_result_validator_dryrun_from_handoff(handoff_manifest_path=_MANIFEST_REL, explicit_overwrite=True)
        self.assertEqual(second["dryrun_status"], "ok")

    def test_dryrun_report_only_under_handoff(self) -> None:
        paths = self._seven_valid_paths()
        self._write_manifest(paths)
        out = run_manual_runtime_result_validator_dryrun_from_handoff(handoff_manifest_path=_MANIFEST_REL)
        self.assertTrue(out["dryrun_report_path"].startswith("docs/evidence/runtime-results/handoff/"))

    def test_no_execute_apply_install_write_delete_release_route(self) -> None:
        routes = (_REPO_ROOT / "backend/deploy/routes.py").read_text(encoding="utf-8")
        self.assertIn("/runner/manual-runtime/result-validator-dryrun-from-handoff", routes)
        for forbidden in [
            "/runner/manual-runtime/result-validator-dryrun-from-handoff/execute",
            "/runner/manual-runtime/result-validator-dryrun-from-handoff/apply",
            "/runner/manual-runtime/result-validator-dryrun-from-handoff/install",
            "/runner/manual-runtime/result-validator-dryrun-from-handoff/write",
            "/runner/manual-runtime/result-validator-dryrun-from-handoff/delete",
            "/runner/manual-runtime/result-validator-dryrun-from-handoff/release",
        ]:
            self.assertNotIn(forbidden, routes)

    def test_no_forbidden_systemcalls(self) -> None:
        src = (_REPO_ROOT / "backend/deploy/runner_manual_runtime_result_validator_dryrun_from_handoff.py").read_text(encoding="utf-8").lower()
        for token in ["subprocess", "os.system", "chmod(", "chown(", "systemctl", " dd ", "mkfs", "mount ", "umount"]:
            self.assertNotIn(token, src)


if __name__ == "__main__":
    unittest.main()
