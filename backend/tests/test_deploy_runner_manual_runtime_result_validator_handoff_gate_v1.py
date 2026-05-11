from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from deploy.runner_manual_runtime_result_bundle_checker import check_manual_runtime_result_bundle
from deploy.runner_manual_runtime_result_validator_handoff_gate import build_manual_runtime_result_validator_handoff

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


class DeployRunnerManualRuntimeResultValidatorHandoffGateV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = _REPO_ROOT / "docs/evidence/runtime-results"
        self.handoff_dir = self.root / "handoff"
        self.root.mkdir(parents=True, exist_ok=True)
        self.manifest = self.handoff_dir / "validator_handoff_manifest.json"
        self.cleanup_paths: list[Path] = []

    def tearDown(self) -> None:
        for p in self.cleanup_paths:
            if p.exists() or p.is_symlink():
                p.unlink()
        if self.manifest.exists():
            self.manifest.unlink()
        for tmp in self.handoff_dir.glob("*.tmp"):
            if tmp.exists():
                tmp.unlink()

    def _write(self, name: str, payload: dict) -> str:
        p = self.root / name
        p.write_text(json.dumps(payload), encoding="utf-8")
        self.cleanup_paths.append(p)
        return str(p.relative_to(_REPO_ROOT))

    def _seven_paths(self) -> list[str]:
        paths: list[str] = []
        for i, rb in enumerate(_SEQUENCE):
            paths.append(self._write(f"h{i}.json", _payload_for(rb)))
        return paths

    def test_ready_bundle_writes_manifest(self) -> None:
        paths = self._seven_paths()
        bundle = check_manual_runtime_result_bundle(result_files=paths)
        self.assertEqual(bundle["bundle_check_status"], "ok")
        out = build_manual_runtime_result_validator_handoff(bundle_check_result=bundle, result_files=paths)
        self.assertEqual(out["handoff_status"], "ready")
        self.assertTrue(self.manifest.is_file())
        data = json.loads(self.manifest.read_text(encoding="utf-8"))
        self.assertEqual(data["validator_input_files"], paths)
        self.assertEqual(out["handoff_manifest_path"], "docs/evidence/runtime-results/handoff/validator_handoff_manifest.json")

    def test_review_required_bundle_is_review_required(self) -> None:
        paths = []
        for i, rb in enumerate(_SEQUENCE):
            pl = _payload_for(rb)
            if i == 2:
                pl["operator"] = ""
            paths.append(self._write(f"rv{i}.json", pl))
        bundle = check_manual_runtime_result_bundle(result_files=paths)
        self.assertEqual(bundle["bundle_check_status"], "review_required")
        out = build_manual_runtime_result_validator_handoff(bundle_check_result=bundle, result_files=paths)
        self.assertEqual(out["handoff_status"], "review_required")
        self.assertFalse(self.manifest.exists())

    def test_blocked_bundle_blocked(self) -> None:
        paths = self._seven_paths()[:5]
        bundle = check_manual_runtime_result_bundle(result_files=paths)
        out = build_manual_runtime_result_validator_handoff(bundle_check_result=bundle, result_files=paths)
        self.assertEqual(out["handoff_status"], "blocked")
        self.assertIn("HANDOFF_BUNDLE_NOT_OK", out["blocked_reasons"])

    def test_missing_result_file_blocked(self) -> None:
        paths = self._seven_paths()
        bundle = check_manual_runtime_result_bundle(result_files=paths)
        Path(self.root / Path(paths[3]).name).unlink()
        out = build_manual_runtime_result_validator_handoff(bundle_check_result=bundle, result_files=paths)
        self.assertEqual(out["handoff_status"], "blocked")
        self.assertIn("HANDOFF_RESULT_FILE_MISSING", out["blocked_reasons"])

    def test_wrong_result_files_count_blocked(self) -> None:
        paths = self._seven_paths()
        bundle = check_manual_runtime_result_bundle(result_files=paths)
        out = build_manual_runtime_result_validator_handoff(bundle_check_result=bundle, result_files=paths[:6])
        self.assertEqual(out["handoff_status"], "blocked")
        self.assertIn("HANDOFF_RESULT_FILES_MISMATCH_VALIDATOR_INPUT", out["blocked_reasons"])

    def test_path_outside_allowed_blocked_tampered_bundle(self) -> None:
        paths = self._seven_paths()
        bundle = check_manual_runtime_result_bundle(result_files=paths)
        bad = list(paths)
        bad[0] = "backend/evil.json"
        b2 = json.loads(json.dumps(bundle))
        b2["validator_bundle_readiness"]["validator_input_files"] = bad
        b2["validator_bundle_readiness"]["ready_for_runtime_result_validator"] = True
        b2["validator_bundle_readiness"]["expected_validator_status"] = "ok"
        out = build_manual_runtime_result_validator_handoff(bundle_check_result=b2, result_files=bad)
        self.assertEqual(out["handoff_status"], "blocked")
        self.assertTrue(any("HANDOFF" in x for x in out["blocked_reasons"]))

    def test_symlink_result_file_blocked(self) -> None:
        paths = self._seven_paths()
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tmp:
            tmp.write(json.dumps(_payload_for(_SEQUENCE[4])))
            ext = tmp.name
        self.addCleanup(lambda: os.path.exists(ext) and os.unlink(ext))
        link = self.root / "symhandoff.json"
        link.symlink_to(ext)
        self.cleanup_paths.append(link)
        tampered = list(paths)
        tampered[4] = str(link.relative_to(_REPO_ROOT))
        bundle = check_manual_runtime_result_bundle(result_files=paths)
        b2 = json.loads(json.dumps(bundle))
        b2["validator_bundle_readiness"]["validator_input_files"] = tampered
        b2["validator_bundle_readiness"]["ready_for_runtime_result_validator"] = True
        out = build_manual_runtime_result_validator_handoff(bundle_check_result=b2, result_files=tampered)
        self.assertEqual(out["handoff_status"], "blocked")
        self.assertIn("HANDOFF_SYMLINK_BLOCKED", out["blocked_reasons"])

    def test_traversal_blocked_tampered(self) -> None:
        paths = self._seven_paths()
        bundle = check_manual_runtime_result_bundle(result_files=paths)
        bad = list(paths)
        bad[1] = "docs/evidence/runtime-results/../runtime-results/x.json"
        b2 = json.loads(json.dumps(bundle))
        b2["validator_bundle_readiness"]["validator_input_files"] = bad
        b2["validator_bundle_readiness"]["ready_for_runtime_result_validator"] = True
        out = build_manual_runtime_result_validator_handoff(bundle_check_result=b2, result_files=bad)
        self.assertEqual(out["handoff_status"], "blocked")

    def test_existing_manifest_blocks_without_overwrite(self) -> None:
        paths = self._seven_paths()
        bundle = check_manual_runtime_result_bundle(result_files=paths)
        self.handoff_dir.mkdir(parents=True, exist_ok=True)
        self.manifest.write_text("{}", encoding="utf-8")
        out = build_manual_runtime_result_validator_handoff(bundle_check_result=bundle, result_files=paths, explicit_overwrite=False)
        self.assertEqual(out["handoff_status"], "blocked")
        self.assertIn("HANDOFF_MANIFEST_EXISTS_NO_OVERWRITE", out["blocked_reasons"])

    def test_explicit_overwrite_replaces_manifest(self) -> None:
        paths = self._seven_paths()
        bundle = check_manual_runtime_result_bundle(result_files=paths)
        self.handoff_dir.mkdir(parents=True, exist_ok=True)
        self.manifest.write_text("{}", encoding="utf-8")
        out = build_manual_runtime_result_validator_handoff(bundle_check_result=bundle, result_files=paths, explicit_overwrite=True)
        self.assertEqual(out["handoff_status"], "ready")
        data = json.loads(self.manifest.read_text(encoding="utf-8"))
        self.assertIn("validator_input_files", data)

    def test_handoff_manifest_only_under_handoff_subpath(self) -> None:
        paths = self._seven_paths()
        bundle = check_manual_runtime_result_bundle(result_files=paths)
        out = build_manual_runtime_result_validator_handoff(bundle_check_result=bundle, result_files=paths)
        self.assertEqual(out["handoff_status"], "ready")
        self.assertTrue(out["handoff_manifest_path"].startswith("docs/evidence/runtime-results/handoff/"))

    def test_no_execute_apply_install_write_delete_release_route(self) -> None:
        routes = (_REPO_ROOT / "backend/deploy/routes.py").read_text(encoding="utf-8")
        self.assertIn("/runner/manual-runtime/result-validator-handoff", routes)
        for forbidden in [
            "/runner/manual-runtime/result-validator-handoff/execute",
            "/runner/manual-runtime/result-validator-handoff/apply",
            "/runner/manual-runtime/result-validator-handoff/install",
            "/runner/manual-runtime/result-validator-handoff/write",
            "/runner/manual-runtime/result-validator-handoff/delete",
            "/runner/manual-runtime/result-validator-handoff/release",
        ]:
            self.assertNotIn(forbidden, routes)

    def test_no_forbidden_systemcalls(self) -> None:
        src = (_REPO_ROOT / "backend/deploy/runner_manual_runtime_result_validator_handoff_gate.py").read_text(encoding="utf-8").lower()
        for token in ["subprocess", "os.system", "chmod(", "chown(", "systemctl", " dd ", "mkfs", "mount ", "umount"]:
            self.assertNotIn(token, src)


if __name__ == "__main__":
    unittest.main()
