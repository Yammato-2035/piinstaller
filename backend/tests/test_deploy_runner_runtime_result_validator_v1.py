from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from deploy.runner_runtime_result_validator import (
    _REPO_ROOT,
    validate_runner_runtime_result_bundle,
)


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


class DeployRunnerRuntimeResultValidatorV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.allowed_dir = _REPO_ROOT / "docs" / "evidence" / "runtime-results"
        self.allowed_dir.mkdir(parents=True, exist_ok=True)
        self.paths: list[Path] = []
        self.sequence = [
            "RUNBOOK_SUDOERS_RUNTIME_DRYRUN",
            "RUNBOOK_PRIVILEGED_RUNNER_VALIDATION_DRYRUN",
            "RUNBOOK_REAL_WRITE_HARDWARE_E2E",
            "RUNBOOK_FAILURE_INJECTION_HARDWARE_E2E",
            "RUNBOOK_DEVICE_REENUMERATION",
            "RUNBOOK_HOTPLUG_UNMOUNT_RACE",
            "RUNBOOK_ROLLBACK_RUNTIME",
        ]

    def tearDown(self) -> None:
        for p in self.paths:
            if p.exists() or p.is_symlink():
                p.unlink()

    def _write(self, name: str, payload: dict) -> str:
        p = self.allowed_dir / name
        p.write_text(json.dumps(payload), encoding="utf-8")
        self.paths.append(p)
        return str(p.relative_to(_REPO_ROOT))

    def _write_invalid_json(self, name: str) -> str:
        p = self.allowed_dir / name
        p.write_text("{not-json", encoding="utf-8")
        self.paths.append(p)
        return str(p.relative_to(_REPO_ROOT))

    def test_valid_7_result_files_ok(self) -> None:
        files = [self._write(f"{idx}.json", _valid_payload(rb)) for idx, rb in enumerate(self.sequence)]
        out = validate_runner_runtime_result_bundle(result_files=files, acceptance_decision="lab_ready_candidate")
        self.assertEqual(out["validation_status"], "ok")
        self.assertEqual(out["blocking_findings"], [])
        self.assertTrue(out["acceptance_check"]["lab_ready_candidate_allowed"])

    def test_missing_required_field_blocked(self) -> None:
        payload = _valid_payload(self.sequence[0])
        del payload["operator"]
        out = validate_runner_runtime_result_bundle(result_files=[self._write("missing-field.json", payload)], acceptance_decision="blocked")
        self.assertEqual(out["validation_status"], "blocked")
        self.assertIn("RESULT_SCHEMA_MISSING_FIELD", out["blocking_findings"])

    def test_invalid_json_blocked(self) -> None:
        out = validate_runner_runtime_result_bundle(result_files=[self._write_invalid_json("invalid.json")], acceptance_decision="blocked")
        self.assertEqual(out["validation_status"], "blocked")
        self.assertIn("RESULT_JSON_INVALID", out["blocking_findings"])

    def test_path_outside_allowed_root_blocked(self) -> None:
        out = validate_runner_runtime_result_bundle(result_files=["backend/tests/evil.json"], acceptance_decision="blocked")
        self.assertEqual(out["validation_status"], "blocked")
        self.assertIn("RESULT_PATH_OUTSIDE_ALLOWED_ROOT", out["blocking_findings"])

    def test_symlink_file_blocked(self) -> None:
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tmp:
            tmp.write(json.dumps(_valid_payload(self.sequence[0])))
            temp_path = tmp.name
        self.addCleanup(lambda: os.path.exists(temp_path) and os.unlink(temp_path))
        link = self.allowed_dir / "symlink.json"
        link.symlink_to(temp_path)
        self.paths.append(link)
        out = validate_runner_runtime_result_bundle(result_files=[str(link.relative_to(_REPO_ROOT))], acceptance_decision="blocked")
        self.assertEqual(out["validation_status"], "blocked")
        self.assertIn("RESULT_SYMLINK_BLOCKED", out["blocking_findings"])

    def test_out_of_order_blocked(self) -> None:
        files = [
            self._write("only-third.json", _valid_payload(self.sequence[2])),
            self._write("second.json", _valid_payload(self.sequence[1])),
        ]
        out = validate_runner_runtime_result_bundle(result_files=files, acceptance_decision="blocked")
        self.assertEqual(out["validation_status"], "blocked")
        self.assertIn("RESULT_SEQUENCE_OUT_OF_ORDER", out["blocking_findings"])

    def test_previous_failed_blocked(self) -> None:
        files = [self._write("0.json", _valid_payload(self.sequence[0], pass_fail="fail"))]
        files.append(self._write("1.json", _valid_payload(self.sequence[1], pass_fail="pass")))
        out = validate_runner_runtime_result_bundle(result_files=files, acceptance_decision="blocked")
        self.assertEqual(out["validation_status"], "blocked")
        self.assertIn("RESULT_PREVIOUS_RUNBOOK_FAILED", out["blocking_findings"])

    def test_missing_evidence_blocked(self) -> None:
        payload = _valid_payload(self.sequence[0])
        del payload["evidence"]["audit_jsonl"]
        out = validate_runner_runtime_result_bundle(result_files=[self._write("missing-evidence.json", payload)], acceptance_decision="blocked")
        self.assertEqual(out["validation_status"], "blocked")
        self.assertIn("RESULT_EVIDENCE_MISSING", out["blocking_findings"])

    def test_verify_mismatch_blocked(self) -> None:
        payload = _valid_payload(self.sequence[2])
        payload["evidence"]["verify_status"] = "mismatch"
        out = validate_runner_runtime_result_bundle(result_files=[self._write("verify-mismatch.json", payload)], acceptance_decision="blocked")
        self.assertEqual(out["validation_status"], "blocked")
        self.assertIn("RESULT_VERIFY_MISMATCH", out["blocking_findings"])

    def test_internal_drive_touched_blocked(self) -> None:
        payload = _valid_payload(self.sequence[2])
        payload["evidence"]["internal_drive_touched"] = True
        out = validate_runner_runtime_result_bundle(result_files=[self._write("internal-drive.json", payload)], acceptance_decision="blocked")
        self.assertEqual(out["validation_status"], "blocked")
        self.assertIn("RESULT_INTERNAL_DRIVE_TOUCHED", out["blocking_findings"])

    def test_untracked_mount_change_blocked(self) -> None:
        payload = _valid_payload(self.sequence[2])
        payload["evidence"]["untracked_mount_change"] = True
        out = validate_runner_runtime_result_bundle(result_files=[self._write("mount-change.json", payload)], acceptance_decision="blocked")
        self.assertEqual(out["validation_status"], "blocked")
        self.assertIn("RESULT_UNTRACKED_MOUNT_CHANGE", out["blocking_findings"])

    def test_rollback_incomplete_blocked(self) -> None:
        payload = _valid_payload(self.sequence[6])
        payload["rollback_status"] = "incomplete"
        out = validate_runner_runtime_result_bundle(result_files=[self._write("rollback-incomplete.json", payload)], acceptance_decision="blocked")
        self.assertEqual(out["validation_status"], "blocked")
        self.assertIn("RESULT_ROLLBACK_INCOMPLETE", out["blocking_findings"])

    def test_lab_ready_candidate_only_with_7_pass(self) -> None:
        files = [self._write("partial.json", _valid_payload(self.sequence[0], pass_fail="pass"))]
        out = validate_runner_runtime_result_bundle(result_files=files, acceptance_decision="lab_ready_candidate")
        self.assertEqual(out["validation_status"], "blocked")
        self.assertFalse(out["acceptance_check"]["lab_ready_candidate_allowed"])

    def test_no_execute_apply_install_write_delete_route(self) -> None:
        routes_path = _REPO_ROOT / "backend" / "deploy" / "routes.py"
        txt = routes_path.read_text(encoding="utf-8")
        self.assertIn("/runner/runtime-results/validate", txt)
        self.assertNotIn("/runner/runtime-results/execute", txt)
        self.assertNotIn("/runner/runtime-results/apply", txt)
        self.assertNotIn("/runner/runtime-results/install", txt)
        self.assertNotIn("/runner/runtime-results/write", txt)
        self.assertNotIn("/runner/runtime-results/delete", txt)

    def test_no_forbidden_systemcalls(self) -> None:
        target = (_REPO_ROOT / "backend" / "deploy" / "runner_runtime_result_validator.py").read_text(encoding="utf-8").lower()
        forbidden = [
            "subprocess",
            "os.system",
            "chmod(",
            "chown(",
            "systemctl",
            " dd ",
            "mkfs",
            "mount ",
            "umount",
        ]
        for token in forbidden:
            self.assertNotIn(token, target)


if __name__ == "__main__":
    unittest.main()
