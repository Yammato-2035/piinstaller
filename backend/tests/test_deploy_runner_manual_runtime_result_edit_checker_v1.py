from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from deploy.runner_manual_runtime_result_edit_checker import check_manual_runtime_result_file

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _base_payload(runbook_id: str = "RUNBOOK_SUDOERS_RUNTIME_DRYRUN") -> dict:
    return {
        "runbook_id": runbook_id,
        "started_at": "2026-05-08T10:00:00Z",
        "completed_at": "2026-05-08T10:05:00Z",
        "operator": "op",
        "host": "lab",
        "target_device": "/dev/sdb",
        "pre_state": {"lsblk": "a", "findmnt": "a", "mount": "a"},
        "post_state": {"lsblk": "b", "findmnt": "b", "mount": "b"},
        "runner_result": {"stdout_json": {"ok": True}, "stderr": "none"},
        "evidence": {
            "audit_jsonl_excerpt": "x",
            "jobfile_hash": "hash",
            "snapshot_fingerprint": "fp",
            "bytes_written": None,
            "expected_sha256": "",
            "actual_sha256": "",
            "verify_status": "",
            "internal_drive_touched": False,
            "untracked_mount_change": False,
        },
        "pass_fail": "pass",
        "rollback_status": "ok",
    }


class DeployRunnerManualRuntimeResultEditCheckerV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = _REPO_ROOT / "docs/evidence/runtime-results"
        self.root.mkdir(parents=True, exist_ok=True)
        self.cleanup_paths: list[Path] = []

    def tearDown(self) -> None:
        for p in self.cleanup_paths:
            if p.exists() or p.is_symlink():
                p.unlink()

    def _write(self, name: str, payload: dict | str) -> str:
        p = self.root / name
        if isinstance(payload, str):
            p.write_text(payload, encoding="utf-8")
        else:
            p.write_text(json.dumps(payload), encoding="utf-8")
        self.cleanup_paths.append(p)
        return str(p.relative_to(_REPO_ROOT))

    def test_valid_file_ok(self) -> None:
        rel = self._write("ok.json", _base_payload())
        out = check_manual_runtime_result_file(result_file=rel)
        self.assertEqual(out["check_status"], "ok")

    def test_empty_template_review_required(self) -> None:
        payload = _base_payload()
        payload["operator"] = ""
        rel = self._write("empty.json", payload)
        out = check_manual_runtime_result_file(result_file=rel)
        self.assertEqual(out["check_status"], "review_required")

    def test_missing_required_field_blocked(self) -> None:
        payload = _base_payload()
        del payload["host"]
        rel = self._write("missing.json", payload)
        out = check_manual_runtime_result_file(result_file=rel)
        self.assertEqual(out["check_status"], "blocked")

    def test_invalid_json_blocked(self) -> None:
        rel = self._write("invalid.json", "{broken")
        out = check_manual_runtime_result_file(result_file=rel)
        self.assertEqual(out["check_status"], "blocked")

    def test_path_outside_allowed_root_blocked(self) -> None:
        out = check_manual_runtime_result_file(result_file="backend/tests/x.json")
        self.assertEqual(out["check_status"], "blocked")

    def test_traversal_blocked(self) -> None:
        out = check_manual_runtime_result_file(result_file="docs/evidence/runtime-results/../x.json")
        self.assertEqual(out["check_status"], "blocked")

    def test_symlink_blocked(self) -> None:
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tmp:
            tmp.write(json.dumps(_base_payload()))
            external = tmp.name
        self.addCleanup(lambda: os.path.exists(external) and os.unlink(external))
        link = self.root / "link.json"
        link.symlink_to(external)
        self.cleanup_paths.append(link)
        out = check_manual_runtime_result_file(result_file=str(link.relative_to(_REPO_ROOT)))
        self.assertEqual(out["check_status"], "blocked")

    def test_internal_drive_touched_blocked(self) -> None:
        payload = _base_payload()
        payload["evidence"]["internal_drive_touched"] = True
        rel = self._write("drive.json", payload)
        out = check_manual_runtime_result_file(result_file=rel)
        self.assertEqual(out["check_status"], "blocked")

    def test_untracked_mount_change_blocked(self) -> None:
        payload = _base_payload()
        payload["evidence"]["untracked_mount_change"] = True
        rel = self._write("umc.json", payload)
        out = check_manual_runtime_result_file(result_file=rel)
        self.assertEqual(out["check_status"], "blocked")

    def test_verify_mismatch_blocked(self) -> None:
        payload = _base_payload("RUNBOOK_REAL_WRITE_HARDWARE_E2E")
        payload["evidence"]["bytes_written"] = 1
        payload["evidence"]["expected_sha256"] = "a"
        payload["evidence"]["actual_sha256"] = "b"
        payload["evidence"]["verify_status"] = "mismatch"
        rel = self._write("mismatch.json", payload)
        out = check_manual_runtime_result_file(result_file=rel)
        self.assertEqual(out["check_status"], "blocked")

    def test_pass_fail_failed_blocked(self) -> None:
        payload = _base_payload()
        payload["pass_fail"] = "failed"
        rel = self._write("failed.json", payload)
        out = check_manual_runtime_result_file(result_file=rel)
        self.assertEqual(out["check_status"], "blocked")

    def test_rollback_incomplete_blocked(self) -> None:
        payload = _base_payload()
        payload["rollback_status"] = "incomplete"
        rel = self._write("rollback.json", payload)
        out = check_manual_runtime_result_file(result_file=rel)
        self.assertEqual(out["check_status"], "blocked")

    def test_stdout_not_object_blocked(self) -> None:
        payload = _base_payload()
        payload["runner_result"]["stdout_json"] = "text"
        rel = self._write("stdout.json", payload)
        out = check_manual_runtime_result_file(result_file=rel)
        self.assertEqual(out["check_status"], "blocked")

    def test_target_device_empty_blocked(self) -> None:
        payload = _base_payload()
        payload["target_device"] = ""
        rel = self._write("target-empty.json", payload)
        out = check_manual_runtime_result_file(result_file=rel)
        self.assertEqual(out["check_status"], "blocked")

    def test_suspicious_target_warns(self) -> None:
        payload = _base_payload()
        payload["target_device"] = "/dev/sda"
        rel = self._write("target-suspicious.json", payload)
        out = check_manual_runtime_result_file(result_file=rel)
        self.assertIn("MANUAL_RESULT_TARGET_DEVICE_SUSPICIOUS", out["warnings"])

    def test_validator_readiness_present(self) -> None:
        rel = self._write("readiness.json", _base_payload())
        out = check_manual_runtime_result_file(result_file=rel)
        self.assertIn("ready_for_ingestion_validator", out["validator_readiness"])

    def test_no_execute_apply_install_write_delete_release_route(self) -> None:
        routes = (_REPO_ROOT / "backend/deploy/routes.py").read_text(encoding="utf-8")
        self.assertIn("/runner/manual-runtime/result-check", routes)
        for forbidden in [
            "/runner/manual-runtime/result-check/execute",
            "/runner/manual-runtime/result-check/apply",
            "/runner/manual-runtime/result-check/install",
            "/runner/manual-runtime/result-check/write",
            "/runner/manual-runtime/result-check/delete",
            "/runner/manual-runtime/result-check/release",
        ]:
            self.assertNotIn(forbidden, routes)

    def test_no_forbidden_systemcalls(self) -> None:
        src = (_REPO_ROOT / "backend/deploy/runner_manual_runtime_result_edit_checker.py").read_text(encoding="utf-8").lower()
        for token in ["subprocess", "os.system", "chmod(", "chown(", "systemctl", " dd ", "mkfs", "mount ", "umount"]:
            self.assertNotIn(token, src)


if __name__ == "__main__":
    unittest.main()
