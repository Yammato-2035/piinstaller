from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

from deploy.runner_manual_runtime_evidence_final_snapshot import build_manual_runtime_evidence_final_snapshot
from deploy.runner_manual_runtime_final_acceptance_gate import evaluate_manual_runtime_final_acceptance
from deploy.runner_manual_runtime_final_export_package import build_manual_runtime_final_export_package

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_TL = _HANDOFF / "validator_evidence_timeline.json"
_SNAP = _HANDOFF / "validator_evidence_final_snapshot.json"
_ACC = _HANDOFF / "validator_final_acceptance.json"
_INDEX = _HANDOFF / "validator_seal_index.json"
_AUDIT = _HANDOFF / "validator_seal_consistency_audit.json"
_DRY = _HANDOFF / "validator_dryrun_report.json"
_SEAL = _HANDOFF / "validator_report.seal.json"
_OUT = _HANDOFF / "validator_final_export_package.json"


def _timeline(events: list[dict], event_count: int | None = None) -> dict:
    ec = event_count if event_count is not None else len(events)
    return {
        "timeline_schema_version": 1,
        "event_count": ec,
        "events": events,
        "generated_at": "2026-05-08T12:00:00Z",
    }


class DeployRunnerManualRuntimeFinalExportPackageV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        for p in [_TL, _SNAP, _ACC, _INDEX, _AUDIT, _DRY, _SEAL, _OUT]:
            p.unlink(missing_ok=True)
        for tmp in _HANDOFF.glob("*.tmp"):
            tmp.unlink(missing_ok=True)

    def tearDown(self) -> None:
        self.setUp()

    def _prepare_chain(self, *, review: bool = False) -> None:
        status = "review_required" if review else "ok"
        _TL.write_text(
            json.dumps(_timeline([{"path": "x", "status": status, "timestamp": "t", "sha256": "a", "event_type": "dryrun_report"}])),
            encoding="utf-8",
        )
        _DRY.write_text(json.dumps({"validator_status": "ok", "report": "x"}), encoding="utf-8")
        _INDEX.write_text(json.dumps({"seal_files": ["docs/evidence/runtime-results/handoff/validator_report.seal.json"]}), encoding="utf-8")
        _AUDIT.write_text(json.dumps({"audit_status": "ok", "findings": []}), encoding="utf-8")
        _SEAL.write_text(
            json.dumps(
                {
                    "source_report": "docs/evidence/runtime-results/handoff/validator_dryrun_report.json",
                    "source_report_sha256": "a" * 64,
                    "sealed_at": "2026-05-08T12:00:00Z",
                    "validator_status": "ok",
                }
            ),
            encoding="utf-8",
        )
        build_manual_runtime_evidence_final_snapshot(explicit_overwrite=True)
        evaluate_manual_runtime_final_acceptance(explicit_overwrite=True)

    def test_accepted_ok(self) -> None:
        self._prepare_chain(review=False)
        out = build_manual_runtime_final_export_package(explicit_overwrite=True)
        self.assertEqual(out["export_package_status"], "ok")
        data = json.loads(_OUT.read_text(encoding="utf-8"))
        self.assertEqual(data["acceptance_status"], "accepted")

    def test_review_required(self) -> None:
        self._prepare_chain(review=True)
        out = build_manual_runtime_final_export_package(explicit_overwrite=True)
        self.assertEqual(out["export_package_status"], "review_required")
        data = json.loads(_OUT.read_text(encoding="utf-8"))
        self.assertEqual(data["acceptance_status"], "review_required")

    def test_blocked_acceptance_blocked(self) -> None:
        self._prepare_chain(review=False)
        acc = json.loads(_ACC.read_text(encoding="utf-8"))
        acc["acceptance_status"] = "blocked"
        _ACC.write_text(json.dumps(acc, indent=2, sort_keys=True), encoding="utf-8")
        out = build_manual_runtime_final_export_package(explicit_overwrite=True)
        self.assertEqual(out["export_package_status"], "blocked")
        self.assertIn("EXPORT_ACCEPTANCE_NOT_ALLOWED", out["blocked_reasons"])

    def test_sha256_correct(self) -> None:
        self._prepare_chain(review=False)
        build_manual_runtime_final_export_package(explicit_overwrite=True)
        data = json.loads(_OUT.read_text(encoding="utf-8"))
        for rel in data["included_files"]:
            raw = (_REPO_ROOT / rel).read_bytes()
            self.assertEqual(data["sha256"][rel], hashlib.sha256(raw).hexdigest())

    def test_missing_file_blocked(self) -> None:
        self._prepare_chain(review=False)
        _AUDIT.unlink(missing_ok=True)
        out = build_manual_runtime_final_export_package(explicit_overwrite=True)
        self.assertEqual(out["export_package_status"], "blocked")
        self.assertTrue(any(str(r).startswith("EXPORT_FILE_MISSING") for r in out["blocked_reasons"]))

    def test_traversal_constant(self) -> None:
        self.assertNotIn("..", Path("docs/evidence/runtime-results/handoff/validator_final_export_package.json").parts)

    def test_symlink_blocked(self) -> None:
        self._prepare_chain(review=False)
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tmp:
            tmp.write("{}")
            ext = tmp.name
        self.addCleanup(lambda: os.path.exists(ext) and os.unlink(ext))
        _DRY.unlink(missing_ok=True)
        _DRY.symlink_to(ext)
        out = build_manual_runtime_final_export_package(explicit_overwrite=True)
        self.assertEqual(out["export_package_status"], "blocked")

    def test_overwrite_blocked(self) -> None:
        self._prepare_chain(review=False)
        build_manual_runtime_final_export_package(explicit_overwrite=True)
        second = build_manual_runtime_final_export_package(explicit_overwrite=False)
        self.assertEqual(second["export_package_status"], "blocked")
        self.assertIn("EXPORT_EXISTS_NO_OVERWRITE", second["blocked_reasons"])

    def test_atomic_no_tmp(self) -> None:
        self._prepare_chain(review=False)
        build_manual_runtime_final_export_package(explicit_overwrite=True)
        self.assertFalse(any(p.name.endswith(".tmp") for p in _HANDOFF.iterdir()))

    def test_no_forbidden_systemcalls(self) -> None:
        src = (_REPO_ROOT / "backend/deploy/runner_manual_runtime_final_export_package.py").read_text(encoding="utf-8").lower()
        for token in ["subprocess", "os.system", "chmod(", "chown(", "systemctl", " dd ", "mkfs", "mount ", "umount"]:
            self.assertNotIn(token, src)

    def test_no_execute_subroutes(self) -> None:
        routes = (_REPO_ROOT / "backend/deploy/routes.py").read_text(encoding="utf-8")
        self.assertIn("/runner/manual-runtime/final-export-package", routes)
        for forbidden in [
            "/runner/manual-runtime/final-export-package/execute",
            "/runner/manual-runtime/final-export-package/apply",
            "/runner/manual-runtime/final-export-package/install",
            "/runner/manual-runtime/final-export-package/write",
            "/runner/manual-runtime/final-export-package/delete",
            "/runner/manual-runtime/final-export-package/release",
        ]:
            self.assertNotIn(forbidden, routes)


if __name__ == "__main__":
    unittest.main()
