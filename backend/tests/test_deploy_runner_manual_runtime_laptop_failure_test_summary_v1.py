from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_manual_runtime_laptop_failure_test_summary import build_manual_laptop_failure_test_summary

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_IN = _HANDOFF / "laptop_failure_execution_log_validation.json"
_OUT = _HANDOFF / "laptop_failure_test_summary.json"


def _rv(run_id: str, st: str, obs: str, issues: list[str] | None = None) -> dict:
    return {
        "run_id": run_id,
        "failure_type": "sha256_mismatch",
        "observed_status": obs,
        "run_validation_status": st,
        "issues": issues or [],
    }


class DeployRunnerManualRuntimeLaptopFailureTestSummaryV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        for p in (_IN, _OUT):
            p.unlink(missing_ok=True)
        for tmp in _HANDOFF.glob("laptop_failure_test_summary.json.tmp"):
            tmp.unlink(missing_ok=True)

    def tearDown(self) -> None:
        self.setUp()

    def _write_validation(self, status: str, runs: list[dict]) -> None:
        _IN.write_text(json.dumps({"validation_status": status, "run_validations": runs}, indent=2), encoding="utf-8")

    def test_ok_summary(self) -> None:
        self._write_validation("ok", [_rv("r1", "ok", "ok")])
        res = build_manual_laptop_failure_test_summary(explicit_overwrite=True)
        self.assertEqual(res.get("summary_status"), "ok")

    def test_review_required_summary(self) -> None:
        self._write_validation("review_required", [_rv("r1", "review_required", "review_required", ["deviation_present"])])
        res = build_manual_laptop_failure_test_summary(explicit_overwrite=True)
        self.assertEqual(res.get("summary_status"), "review_required")

    def test_blocked_summary(self) -> None:
        self._write_validation("blocked", [_rv("r1", "blocked", "blocked")])
        res = build_manual_laptop_failure_test_summary(explicit_overwrite=True)
        self.assertEqual(res.get("summary_status"), "blocked")

    def test_counts_korrekt(self) -> None:
        self._write_validation(
            "review_required",
            [
                _rv("r1", "ok", "ok"),
                _rv("r2", "review_required", "review_required", ["deviation_detected"]),
                _rv("r3", "blocked", "blocked", ["invalid_abort_triggered"]),
            ],
        )
        res = build_manual_laptop_failure_test_summary(explicit_overwrite=True)
        self.assertEqual(res.get("total_runs"), 3)
        self.assertEqual(res.get("ok_runs"), 1)
        self.assertEqual(res.get("review_required_runs"), 1)
        self.assertEqual(res.get("blocked_runs"), 1)
        self.assertEqual(res.get("abort_count"), 1)
        self.assertEqual(res.get("deviation_count"), 1)

    def test_overwrite_blockiert(self) -> None:
        self._write_validation("ok", [_rv("r1", "ok", "ok")])
        first = build_manual_laptop_failure_test_summary(explicit_overwrite=True)
        self.assertEqual(first.get("summary_status"), "ok")
        second = build_manual_laptop_failure_test_summary(explicit_overwrite=False)
        self.assertEqual(second.get("summary_status"), "blocked")
        self.assertIn("TEST_SUMMARY_EXISTS_NO_OVERWRITE", second.get("blocked_reasons") or [])

    def test_atomisches_schreiben(self) -> None:
        self._write_validation("ok", [_rv("r1", "ok", "ok")])
        build_manual_laptop_failure_test_summary(explicit_overwrite=True)
        self.assertTrue(_OUT.is_file())
        self.assertFalse((_HANDOFF / "laptop_failure_test_summary.json.tmp").exists())

    def test_keine_verbotenen_systemcalls(self) -> None:
        src = Path(__file__).resolve().parents[1] / "deploy" / "runner_manual_runtime_laptop_failure_test_summary.py"
        text = src.read_text(encoding="utf-8")
        self.assertNotIn("subprocess", text)
        self.assertNotIn("os.system", text)

    def test_keine_verbotenen_unterrouten(self) -> None:
        routes = Path(__file__).resolve().parents[1] / "deploy" / "routes.py"
        chunk = routes.read_text(encoding="utf-8")
        start = chunk.find("laptop-failure-test-summary")
        self.assertGreater(start, 0)
        block = chunk[start : start + 1000]
        self.assertIn("build_manual_laptop_failure_test_summary", block)
        self.assertNotIn("execute_deploy", block)
        self.assertNotIn("execute_deploy_write", block)


if __name__ == "__main__":
    unittest.main()
