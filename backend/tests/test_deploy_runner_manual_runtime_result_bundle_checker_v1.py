from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from deploy.runner_manual_runtime_result_bundle_checker import check_manual_runtime_result_bundle

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

_WRITE = {
    "RUNBOOK_REAL_WRITE_HARDWARE_E2E",
    "RUNBOOK_FAILURE_INJECTION_HARDWARE_E2E",
    "RUNBOOK_DEVICE_REENUMERATION",
    "RUNBOOK_HOTPLUG_UNMOUNT_RACE",
    "RUNBOOK_ROLLBACK_RUNTIME",
}


def _base_payload(runbook_id: str) -> dict:
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
            "internal_drive_touched": False,
            "untracked_mount_change": False,
        },
        "pass_fail": "pass",
        "rollback_status": "ok",
    }


def _payload_for(rb: str) -> dict:
    p = _base_payload(rb)
    ev = p["evidence"]
    if rb in _WRITE:
        ev["bytes_written"] = 1
        ev["expected_sha256"] = "a" * 64
        ev["actual_sha256"] = "a" * 64
        ev["verify_status"] = "match"
    else:
        ev["bytes_written"] = None
        ev["expected_sha256"] = ""
        ev["actual_sha256"] = ""
        ev["verify_status"] = ""
    return p


class DeployRunnerManualRuntimeResultBundleCheckerV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = _REPO_ROOT / "docs/evidence/runtime-results"
        self.root.mkdir(parents=True, exist_ok=True)
        self.cleanup_paths: list[Path] = []

    def tearDown(self) -> None:
        for p in self.cleanup_paths:
            if p.exists() or p.is_symlink():
                p.unlink()

    def _write(self, name: str, payload: dict) -> str:
        p = self.root / name
        p.write_text(json.dumps(payload), encoding="utf-8")
        self.cleanup_paths.append(p)
        return str(p.relative_to(_REPO_ROOT))

    def _seven_paths(self) -> list[str]:
        paths: list[str] = []
        for i, rb in enumerate(_SEQUENCE):
            paths.append(self._write(f"b{i}.json", _payload_for(rb)))
        return paths

    def test_valid_seven_ok(self) -> None:
        paths = self._seven_paths()
        out = check_manual_runtime_result_bundle(result_files=paths)
        self.assertEqual(out["bundle_check_status"], "ok")
        self.assertEqual(out["bundle_findings"], [])
        vr = out["validator_bundle_readiness"]
        self.assertTrue(vr["ready_for_runtime_result_validator"])
        self.assertEqual(vr["expected_validator_status"], "ok")
        self.assertEqual(vr["validator_input_files"], paths)

    def test_missing_runbook_blocked(self) -> None:
        paths = self._seven_paths()[:6]
        out = check_manual_runtime_result_bundle(result_files=paths)
        self.assertEqual(out["bundle_check_status"], "blocked")
        self.assertIn("BUNDLE_RESULT_MISSING_RUNBOOK", out["bundle_findings"])

    def test_unknown_runbook_blocked(self) -> None:
        paths = self._seven_paths()
        bad = dict(_payload_for(_SEQUENCE[3]))
        bad["runbook_id"] = "RUNBOOK_UNKNOWN_X"
        paths[3] = self._write("unknown.json", bad)
        out = check_manual_runtime_result_bundle(result_files=paths)
        self.assertEqual(out["bundle_check_status"], "blocked")
        self.assertIn("BUNDLE_RESULT_UNKNOWN_RUNBOOK", out["bundle_findings"])

    def test_duplicate_runbook_blocked(self) -> None:
        paths = []
        for i in range(7):
            rb = _SEQUENCE[1] if i == 6 else _SEQUENCE[i]
            paths.append(self._write(f"d{i}.json", _payload_for(rb)))
        out = check_manual_runtime_result_bundle(result_files=paths)
        self.assertEqual(out["bundle_check_status"], "blocked")
        self.assertIn("BUNDLE_RESULT_DUPLICATE_RUNBOOK", out["bundle_findings"])

    def test_out_of_order_blocked(self) -> None:
        paths = []
        order = [_SEQUENCE[1], _SEQUENCE[0]] + list(_SEQUENCE[2:])
        for i, rb in enumerate(order):
            paths.append(self._write(f"o{i}.json", _payload_for(rb)))
        out = check_manual_runtime_result_bundle(result_files=paths)
        self.assertEqual(out["bundle_check_status"], "blocked")
        self.assertIn("BUNDLE_RESULT_SEQUENCE_OUT_OF_ORDER", out["bundle_findings"])

    def test_previous_runbook_not_pass_blocked(self) -> None:
        paths = []
        for i, rb in enumerate(_SEQUENCE):
            pl = _payload_for(rb)
            if i == 0:
                pl["pass_fail"] = "failed"
            elif i == 1:
                pl["pass_fail"] = "pass"
            paths.append(self._write(f"p{i}.json", pl))
        out = check_manual_runtime_result_bundle(result_files=paths)
        self.assertEqual(out["bundle_check_status"], "blocked")
        self.assertIn("BUNDLE_RESULT_PREVIOUS_RUNBOOK_NOT_PASS", out["bundle_findings"])

    def test_one_file_review_bundle_review(self) -> None:
        paths = []
        for i, rb in enumerate(_SEQUENCE):
            pl = _payload_for(rb)
            if i == 3:
                pl["operator"] = ""
            paths.append(self._write(f"r{i}.json", pl))
        out = check_manual_runtime_result_bundle(result_files=paths)
        self.assertEqual(out["bundle_check_status"], "review_required")

    def test_one_file_blocked_bundle_blocked(self) -> None:
        paths = []
        for i, rb in enumerate(_SEQUENCE):
            pl = _payload_for(rb)
            if i == 2:
                del pl["host"]
            paths.append(self._write(f"x{i}.json", pl))
        out = check_manual_runtime_result_bundle(result_files=paths)
        self.assertEqual(out["bundle_check_status"], "blocked")

    def test_internal_drive_touched_blocked(self) -> None:
        paths = self._seven_paths()
        p = json.loads((self.root / Path(paths[4]).name).read_text(encoding="utf-8"))
        p["evidence"]["internal_drive_touched"] = True
        (self.root / Path(paths[4]).name).write_text(json.dumps(p), encoding="utf-8")
        out = check_manual_runtime_result_bundle(result_files=paths)
        self.assertEqual(out["bundle_check_status"], "blocked")
        self.assertIn("BUNDLE_INTERNAL_DRIVE_TOUCHED", out["bundle_findings"])

    def test_untracked_mount_change_blocked(self) -> None:
        paths = self._seven_paths()
        p = json.loads((self.root / Path(paths[3]).name).read_text(encoding="utf-8"))
        p["evidence"]["untracked_mount_change"] = True
        (self.root / Path(paths[3]).name).write_text(json.dumps(p), encoding="utf-8")
        out = check_manual_runtime_result_bundle(result_files=paths)
        self.assertEqual(out["bundle_check_status"], "blocked")
        self.assertIn("BUNDLE_UNTRACKED_MOUNT_CHANGE", out["bundle_findings"])

    def test_verify_mismatch_blocked(self) -> None:
        paths = self._seven_paths()
        p = json.loads((self.root / Path(paths[2]).name).read_text(encoding="utf-8"))
        p["evidence"]["verify_status"] = "mismatch"
        (self.root / Path(paths[2]).name).write_text(json.dumps(p), encoding="utf-8")
        out = check_manual_runtime_result_bundle(result_files=paths)
        self.assertEqual(out["bundle_check_status"], "blocked")
        self.assertIn("BUNDLE_VERIFY_MISMATCH", out["bundle_findings"])

    def test_write_evidence_missing_blocked(self) -> None:
        paths = []
        for i, rb in enumerate(_SEQUENCE):
            pl = _payload_for(rb)
            if rb == "RUNBOOK_REAL_WRITE_HARDWARE_E2E":
                del pl["evidence"]["expected_sha256"]
            paths.append(self._write(f"w{i}.json", pl))
        out = check_manual_runtime_result_bundle(result_files=paths)
        self.assertEqual(out["bundle_check_status"], "blocked")
        self.assertIn("BUNDLE_WRITE_EVIDENCE_MISSING", out["bundle_findings"])

    def test_audit_missing_blocked(self) -> None:
        paths = self._seven_paths()
        p = json.loads((self.root / Path(paths[1]).name).read_text(encoding="utf-8"))
        p["evidence"]["audit_jsonl_excerpt"] = ""
        (self.root / Path(paths[1]).name).write_text(json.dumps(p), encoding="utf-8")
        out = check_manual_runtime_result_bundle(result_files=paths)
        self.assertEqual(out["bundle_check_status"], "blocked")
        self.assertIn("BUNDLE_AUDIT_MISSING", out["bundle_findings"])

    def test_job_hash_missing_blocked(self) -> None:
        paths = self._seven_paths()
        p = json.loads((self.root / Path(paths[5]).name).read_text(encoding="utf-8"))
        p["evidence"]["jobfile_hash"] = ""
        (self.root / Path(paths[5]).name).write_text(json.dumps(p), encoding="utf-8")
        out = check_manual_runtime_result_bundle(result_files=paths)
        self.assertEqual(out["bundle_check_status"], "blocked")
        self.assertIn("BUNDLE_JOB_HASH_MISSING", out["bundle_findings"])

    def test_fingerprint_missing_blocked(self) -> None:
        paths = self._seven_paths()
        p = json.loads((self.root / Path(paths[6]).name).read_text(encoding="utf-8"))
        p["evidence"]["snapshot_fingerprint"] = " "
        (self.root / Path(paths[6]).name).write_text(json.dumps(p), encoding="utf-8")
        out = check_manual_runtime_result_bundle(result_files=paths)
        self.assertEqual(out["bundle_check_status"], "blocked")
        self.assertIn("BUNDLE_FINGERPRINT_MISSING", out["bundle_findings"])

    def test_validator_bundle_readiness_not_ready_when_blocked(self) -> None:
        paths = self._seven_paths()[:5]
        out = check_manual_runtime_result_bundle(result_files=paths)
        vr = out["validator_bundle_readiness"]
        self.assertFalse(vr["ready_for_runtime_result_validator"])
        self.assertEqual(vr["expected_validator_status"], "blocked")

    def test_path_outside_blocked(self) -> None:
        paths = self._seven_paths()
        paths[0] = "backend/tests/x.json"
        out = check_manual_runtime_result_bundle(result_files=paths)
        self.assertEqual(out["bundle_check_status"], "blocked")

    def test_traversal_blocked(self) -> None:
        paths = self._seven_paths()
        paths[1] = "docs/evidence/runtime-results/../x.json"
        out = check_manual_runtime_result_bundle(result_files=paths)
        self.assertEqual(out["bundle_check_status"], "blocked")

    def test_symlink_blocked(self) -> None:
        paths = self._seven_paths()
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tmp:
            tmp.write(json.dumps(_payload_for(_SEQUENCE[2])))
            external = tmp.name
        self.addCleanup(lambda: os.path.exists(external) and os.unlink(external))
        link = self.root / "symlink_bundle.json"
        link.symlink_to(external)
        self.cleanup_paths.append(link)
        paths[2] = str(link.relative_to(_REPO_ROOT))
        out = check_manual_runtime_result_bundle(result_files=paths)
        self.assertEqual(out["bundle_check_status"], "blocked")

    def test_no_execute_apply_install_write_delete_release_route(self) -> None:
        routes = (_REPO_ROOT / "backend/deploy/routes.py").read_text(encoding="utf-8")
        self.assertIn("/runner/manual-runtime/result-bundle-check", routes)
        for forbidden in [
            "/runner/manual-runtime/result-bundle-check/execute",
            "/runner/manual-runtime/result-bundle-check/apply",
            "/runner/manual-runtime/result-bundle-check/install",
            "/runner/manual-runtime/result-bundle-check/write",
            "/runner/manual-runtime/result-bundle-check/delete",
            "/runner/manual-runtime/result-bundle-check/release",
        ]:
            self.assertNotIn(forbidden, routes)

    def test_no_forbidden_systemcalls(self) -> None:
        src = (_REPO_ROOT / "backend/deploy/runner_manual_runtime_result_bundle_checker.py").read_text(encoding="utf-8").lower()
        for token in ["subprocess", "os.system", "chmod(", "chown(", "systemctl", " dd ", "mkfs", "mount ", "umount"]:
            self.assertNotIn(token, src)


if __name__ == "__main__":
    unittest.main()
