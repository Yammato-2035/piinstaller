from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from deploy.runner_manual_runtime_laptop_failure_final_report import build_manual_laptop_failure_final_report

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_SUMMARY = _HANDOFF / "laptop_failure_test_summary.json"
_REPORT = _HANDOFF / "laptop_failure_final_report.json"


def _summary(status: str) -> dict:
    return {
        "summary_schema_version": 1,
        "strict_mode": "laptop_failure_test_summary",
        "generated_at": "2026-05-09T09:00:00Z",
        "summary_status": status,
        "total_runs": 1,
        "ok_runs": 1 if status == "ok" else 0,
        "review_required_runs": 1 if status == "review_required" else 0,
        "blocked_runs": 1 if status == "blocked" else 0,
        "abort_count": 0,
        "deviation_count": 0,
        "findings": [],
    }


class DeployRunnerManualRuntimeLaptopFailureFinalReportV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        for p in (_SUMMARY, _REPORT):
            p.unlink(missing_ok=True)
        for tmp in _HANDOFF.glob("laptop_failure_final_report.json.tmp"):
            tmp.unlink(missing_ok=True)

    def tearDown(self) -> None:
        self.setUp()

    def _write_summary(self, status: str) -> bytes:
        raw = json.dumps(_summary(status), indent=2, sort_keys=True).encode("utf-8")
        _SUMMARY.write_bytes(raw)
        return raw

    def test_ok_report(self) -> None:
        raw = self._write_summary("ok")
        res = build_manual_laptop_failure_final_report(explicit_overwrite=True)
        self.assertEqual(res.get("report_status"), "ok")
        self.assertEqual(res.get("recommendation"), "proceed")
        self.assertEqual(res.get("summary_sha256"), hashlib.sha256(raw).hexdigest())

    def test_review_required_report(self) -> None:
        self._write_summary("review_required")
        res = build_manual_laptop_failure_final_report(explicit_overwrite=True)
        self.assertEqual(res.get("report_status"), "review_required")
        self.assertEqual(res.get("recommendation"), "review_before_next_run")

    def test_blocked_report(self) -> None:
        self._write_summary("blocked")
        res = build_manual_laptop_failure_final_report(explicit_overwrite=True)
        self.assertEqual(res.get("report_status"), "blocked")
        self.assertEqual(res.get("recommendation"), "blocked")

    def test_overwrite_blockiert(self) -> None:
        self._write_summary("ok")
        first = build_manual_laptop_failure_final_report(explicit_overwrite=True)
        self.assertEqual(first.get("report_status"), "ok")
        second = build_manual_laptop_failure_final_report(explicit_overwrite=False)
        self.assertEqual(second.get("report_status"), "blocked")
        self.assertIn("FINAL_REPORT_EXISTS_NO_OVERWRITE", second.get("blocked_reasons") or [])

    def test_atomisches_schreiben(self) -> None:
        self._write_summary("ok")
        build_manual_laptop_failure_final_report(explicit_overwrite=True)
        self.assertTrue(_REPORT.is_file())
        self.assertFalse((_HANDOFF / "laptop_failure_final_report.json.tmp").exists())

    def test_keine_verbotenen_systemcalls(self) -> None:
        src = Path(__file__).resolve().parents[1] / "deploy" / "runner_manual_runtime_laptop_failure_final_report.py"
        text = src.read_text(encoding="utf-8")
        self.assertNotIn("subprocess", text)
        self.assertNotIn("os.system", text)

    def test_keine_verbotenen_unterrouten(self) -> None:
        routes = Path(__file__).resolve().parents[1] / "deploy" / "routes.py"
        chunk = routes.read_text(encoding="utf-8")
        start = chunk.find("laptop-failure-final-report")
        self.assertGreater(start, 0)
        block = chunk[start : start + 1000]
        self.assertIn("build_manual_laptop_failure_final_report", block)
        self.assertNotIn("execute_deploy", block)
        self.assertNotIn("execute_deploy_write", block)


if __name__ == "__main__":
    unittest.main()
