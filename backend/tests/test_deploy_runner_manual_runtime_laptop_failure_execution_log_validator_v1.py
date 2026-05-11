from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_manual_runtime_laptop_failure_execution_log_validator import (
    validate_manual_laptop_failure_execution_log,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_IN = _HANDOFF / "laptop_failure_execution_log.json"
_OUT = _HANDOFF / "laptop_failure_execution_log_validation.json"


def _run(
    rid: str,
    ft: str,
    *,
    obs: str = "ok",
    deviations: list | None = None,
    abort_triggered: bool = False,
    destructive: bool = False,
) -> dict:
    return {
        "run_id": rid,
        "failure_type": ft,
        "operator_step_index": 1,
        "started_at": "2026-05-09T08:00:00Z",
        "completed_at": "2026-05-09T08:10:00Z",
        "operator": "op1",
        "host": "host1",
        "test_media": "usb-test",
        "pre_state": {"lsblk": "ok", "findmnt": "ok", "mount": "ok"},
        "observed_detection": "hash_guard",
        "observed_status": obs,
        "evidence_collected": ["log1"],
        "abort_triggered": abort_triggered,
        "abort_reason": "manual_stop" if abort_triggered else "",
        "rollback_performed": False,
        "post_state": {"lsblk": "ok", "findmnt": "ok", "mount": "ok"},
        "deviations": deviations if deviations is not None else [],
        "notes": [],
        "destructive": destructive,
    }


class DeployRunnerManualRuntimeLaptopFailureExecutionLogValidatorV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        for p in (_IN, _OUT):
            p.unlink(missing_ok=True)
        for tmp in _HANDOFF.glob("laptop_failure_execution_log_validation.json.tmp"):
            tmp.unlink(missing_ok=True)

    def tearDown(self) -> None:
        self.setUp()

    def _write_input(self, runs: list[dict]) -> None:
        _IN.write_text(json.dumps({"ordered_runs": runs}, indent=2), encoding="utf-8")

    def test_vollstaendiges_log_ok(self) -> None:
        self._write_input([_run("r1", "sha256_mismatch", obs="ok")])
        res = validate_manual_laptop_failure_execution_log(explicit_overwrite=True)
        self.assertEqual(res.get("validation_status"), "ok")

    def test_deviations_review_required(self) -> None:
        self._write_input([_run("r1", "sha256_mismatch", obs="ok", deviations=["delta"])])
        res = validate_manual_laptop_failure_execution_log(explicit_overwrite=True)
        self.assertEqual(res.get("validation_status"), "review_required")

    def test_abort_triggered_review_required(self) -> None:
        self._write_input([_run("r1", "sha256_mismatch", obs="ok", abort_triggered=True)])
        res = validate_manual_laptop_failure_execution_log(explicit_overwrite=True)
        self.assertEqual(res.get("validation_status"), "review_required")

    def test_observed_status_blocked(self) -> None:
        self._write_input([_run("r1", "sha256_mismatch", obs="blocked")])
        res = validate_manual_laptop_failure_execution_log(explicit_overwrite=True)
        self.assertEqual(res.get("validation_status"), "blocked")

    def test_fehlende_pflichtfelder_blocked(self) -> None:
        bad = _run("r1", "sha256_mismatch", obs="ok")
        bad["operator"] = ""
        self._write_input([bad])
        res = validate_manual_laptop_failure_execution_log(explicit_overwrite=True)
        self.assertEqual(res.get("validation_status"), "blocked")

    def test_destructive_true_blocked(self) -> None:
        self._write_input([_run("r1", "sha256_mismatch", destructive=True)])
        res = validate_manual_laptop_failure_execution_log(explicit_overwrite=True)
        self.assertEqual(res.get("validation_status"), "blocked")

    def test_overwrite_blockiert(self) -> None:
        self._write_input([_run("r1", "sha256_mismatch")])
        first = validate_manual_laptop_failure_execution_log(explicit_overwrite=True)
        self.assertEqual(first.get("validation_status"), "ok")
        second = validate_manual_laptop_failure_execution_log(explicit_overwrite=False)
        self.assertEqual(second.get("validation_status"), "blocked")
        self.assertIn("EXEC_LOG_VALIDATION_EXISTS_NO_OVERWRITE", second.get("blocked_reasons") or [])

    def test_atomisches_schreiben(self) -> None:
        self._write_input([_run("r1", "sha256_mismatch")])
        validate_manual_laptop_failure_execution_log(explicit_overwrite=True)
        self.assertTrue(_OUT.is_file())
        self.assertFalse((_HANDOFF / "laptop_failure_execution_log_validation.json.tmp").exists())

    def test_keine_verbotenen_systemcalls(self) -> None:
        src = Path(__file__).resolve().parents[1] / "deploy" / "runner_manual_runtime_laptop_failure_execution_log_validator.py"
        text = src.read_text(encoding="utf-8")
        self.assertNotIn("subprocess", text)
        self.assertNotIn("os.system", text)

    def test_keine_verbotenen_unterrouten(self) -> None:
        routes = Path(__file__).resolve().parents[1] / "deploy" / "routes.py"
        chunk = routes.read_text(encoding="utf-8")
        start = chunk.find("laptop-failure-execution-log-validation")
        self.assertGreater(start, 0)
        block = chunk[start : start + 1000]
        self.assertIn("validate_manual_laptop_failure_execution_log", block)
        self.assertNotIn("execute_deploy", block)
        self.assertNotIn("execute_deploy_write", block)


if __name__ == "__main__":
    unittest.main()
