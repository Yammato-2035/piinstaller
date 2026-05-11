from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

from deploy.runner_manual_runtime_validator_report_seal import seal_manual_runtime_validator_report

_REPO_ROOT = Path(__file__).resolve().parents[2]
_REPORT = "docs/evidence/runtime-results/handoff/validator_dryrun_report.json"
_SEAL = "docs/evidence/runtime-results/handoff/validator_dryrun_report.seal.json"


def _minimal_ok_report() -> dict:
    return {
        "dryrun_schema_version": 1,
        "dryrun_status": "ok",
        "validator_result": {"validation_status": "ok", "result_files": []},
    }


class DeployRunnerManualRuntimeValidatorReportSealV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.handoff = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
        self.handoff.mkdir(parents=True, exist_ok=True)
        self.report_path = self.handoff / "validator_dryrun_report.json"
        self.seal_path = self.handoff / "validator_dryrun_report.seal.json"

    def tearDown(self) -> None:
        for p in (self.report_path, self.seal_path):
            if p.exists():
                p.unlink()
        sym = self.handoff / "sym_report.json"
        if sym.exists() or sym.is_symlink():
            sym.unlink()
        for tmp in self.handoff.glob("*.tmp"):
            tmp.unlink(missing_ok=True)

    def test_valid_dryrun_creates_seal(self) -> None:
        body = _minimal_ok_report()
        raw = json.dumps(body, indent=2).encode("utf-8")
        self.report_path.write_bytes(raw)
        out = seal_manual_runtime_validator_report(dryrun_report_path=_REPORT, explicit_overwrite=False)
        self.assertEqual(out["seal_status"], "sealed")
        self.assertEqual(out["seal_file_path"], _SEAL)
        self.assertEqual(out["sealed_sha256"], hashlib.sha256(raw).hexdigest())
        seal = json.loads(self.seal_path.read_text(encoding="utf-8"))
        self.assertEqual(seal["source_report_sha256"], out["sealed_sha256"])

    def test_dryrun_not_ok_blocked(self) -> None:
        body = _minimal_ok_report()
        body["dryrun_status"] = "blocked"
        self.report_path.write_text(json.dumps(body), encoding="utf-8")
        out = seal_manual_runtime_validator_report(dryrun_report_path=_REPORT)
        self.assertEqual(out["seal_status"], "blocked")
        self.assertIn("SEAL_DRYRUN_STATUS_NOT_OK", out["blocked_reasons"])

    def test_missing_report_blocked(self) -> None:
        if self.report_path.exists():
            self.report_path.unlink()
        out = seal_manual_runtime_validator_report(dryrun_report_path=_REPORT)
        self.assertEqual(out["seal_status"], "blocked")

    def test_traversal_blocked(self) -> None:
        out = seal_manual_runtime_validator_report(
            dryrun_report_path="docs/evidence/runtime-results/handoff/../handoff/x.json",
        )
        self.assertEqual(out["seal_status"], "blocked")

    def test_symlink_report_blocked(self) -> None:
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tmp:
            tmp.write(json.dumps(_minimal_ok_report()))
            ext = tmp.name
        self.addCleanup(lambda: os.path.exists(ext) and os.unlink(ext))
        link = self.handoff / "sym_report.json"
        link.symlink_to(ext)
        rel = str(link.relative_to(_REPO_ROOT))
        out = seal_manual_runtime_validator_report(dryrun_report_path=rel)
        self.assertEqual(out["seal_status"], "blocked")
        self.assertIn("SEAL_SYMLINK_BLOCKED", out["blocked_reasons"])

    def test_existing_seal_blocks_without_overwrite(self) -> None:
        body = _minimal_ok_report()
        self.report_path.write_text(json.dumps(body), encoding="utf-8")
        first = seal_manual_runtime_validator_report(dryrun_report_path=_REPORT)
        self.assertEqual(first["seal_status"], "sealed")
        second = seal_manual_runtime_validator_report(dryrun_report_path=_REPORT, explicit_overwrite=False)
        self.assertEqual(second["seal_status"], "blocked")
        self.assertIn("SEAL_EXISTS_NO_OVERWRITE", second["blocked_reasons"])

    def test_explicit_overwrite_rewrites_seal(self) -> None:
        body = _minimal_ok_report()
        self.report_path.write_text(json.dumps(body), encoding="utf-8")
        seal_manual_runtime_validator_report(dryrun_report_path=_REPORT)
        out = seal_manual_runtime_validator_report(dryrun_report_path=_REPORT, explicit_overwrite=True)
        self.assertEqual(out["seal_status"], "sealed")

    def test_sha256_stable(self) -> None:
        body = _minimal_ok_report()
        raw = json.dumps(body, sort_keys=True).encode("utf-8")
        self.report_path.write_bytes(raw)
        a = seal_manual_runtime_validator_report(dryrun_report_path=_REPORT, explicit_overwrite=True)
        b = seal_manual_runtime_validator_report(dryrun_report_path=_REPORT, explicit_overwrite=True)
        self.assertEqual(a["sealed_sha256"], b["sealed_sha256"])

    def test_atomic_write_no_tmp_left(self) -> None:
        body = _minimal_ok_report()
        self.report_path.write_text(json.dumps(body), encoding="utf-8")
        seal_manual_runtime_validator_report(dryrun_report_path=_REPORT)
        self.assertFalse(any(p.name.endswith(".tmp") for p in self.handoff.iterdir()))

    def test_seal_only_under_handoff(self) -> None:
        body = _minimal_ok_report()
        self.report_path.write_text(json.dumps(body), encoding="utf-8")
        out = seal_manual_runtime_validator_report(dryrun_report_path=_REPORT)
        self.assertTrue(out["seal_file_path"].startswith("docs/evidence/runtime-results/handoff/"))

    def test_no_forbidden_systemcalls(self) -> None:
        src = (_REPO_ROOT / "backend/deploy/runner_manual_runtime_validator_report_seal.py").read_text(encoding="utf-8").lower()
        for token in ["subprocess", "os.system", "chmod(", "chown(", "systemctl", " dd ", "mkfs", "mount ", "umount"]:
            self.assertNotIn(token, src)

    def test_no_execute_subroutes(self) -> None:
        routes = (_REPO_ROOT / "backend/deploy/routes.py").read_text(encoding="utf-8")
        self.assertIn("/runner/manual-runtime/result-validator-report-seal", routes)
        for forbidden in [
            "/runner/manual-runtime/result-validator-report-seal/execute",
            "/runner/manual-runtime/result-validator-report-seal/apply",
            "/runner/manual-runtime/result-validator-report-seal/install",
            "/runner/manual-runtime/result-validator-report-seal/write",
            "/runner/manual-runtime/result-validator-report-seal/delete",
            "/runner/manual-runtime/result-validator-report-seal/release",
        ]:
            self.assertNotIn(forbidden, routes)


if __name__ == "__main__":
    unittest.main()
