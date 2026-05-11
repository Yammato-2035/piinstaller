from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_manual_runtime_laptop_failure_operator_runorder import build_manual_laptop_failure_operator_runorder

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_SEL = _HANDOFF / "laptop_failure_run_selection.json"
_RO = _HANDOFF / "laptop_failure_operator_runorder.json"


def _run(
    sid: str,
    ft: str,
    *,
    risk: str = "low",
    rb: bool = False,
    pk: list | None = None,
    destructive: bool | None = None,
    abort: list | None = None,
    evidence: list | None = None,
    mode: str = "manual_only",
) -> dict:
    r: dict = {
        "session_id": sid,
        "failure_type": ft,
        "execution_mode": mode,
        "risk_level": risk,
        "rollback_required": rb,
        "abort_conditions": abort if abort is not None else ["abort1"],
        "evidence_to_capture": evidence if evidence is not None else ["ev1"],
        "priority_key": pk if pk is not None else [0, 0, 0, 0, ft],
    }
    if destructive is not None:
        r["destructive"] = destructive
    return r


class DeployRunnerManualRuntimeLaptopFailureOperatorRunorderV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        for p in (_SEL, _RO):
            p.unlink(missing_ok=True)
        for tmp in _HANDOFF.glob("laptop_failure_operator_runorder.json.tmp"):
            tmp.unlink(missing_ok=True)

    def tearDown(self) -> None:
        self.setUp()

    def _write_selection(self, **kwargs: object) -> None:
        _SEL.write_text(json.dumps(kwargs, indent=2), encoding="utf-8")

    def test_ready_produces_runorder(self) -> None:
        self._write_selection(
            selection_schema_version=1,
            selection_status="ready",
            selected_runs=[_run("s1", "case_plain")],
            deferred_runs=[],
            warnings=[],
            blocked_reasons=[],
        )
        r = build_manual_laptop_failure_operator_runorder(explicit_overwrite=True)
        self.assertEqual(r.get("runorder_status"), "ready")
        self.assertEqual(len(r.get("ordered_runs") or []), 1)
        self.assertEqual(r["ordered_runs"][0]["operator_step_index"], 1)
        doc = json.loads(_RO.read_text(encoding="utf-8"))
        self.assertEqual(doc["runorder_status"], "ready")

    def test_review_required_with_warning(self) -> None:
        self._write_selection(
            selection_status="review_required",
            selected_runs=[_run("s1", "case_plain")],
            deferred_runs=[],
            warnings=[],
            blocked_reasons=[],
        )
        r = build_manual_laptop_failure_operator_runorder(explicit_overwrite=True)
        self.assertEqual(r.get("runorder_status"), "review_required")
        self.assertIn("upstream_selection_review_required", r.get("warnings") or [])

    def test_blocked_selection_blocks(self) -> None:
        self._write_selection(
            selection_status="blocked",
            selected_runs=[_run("s1", "case_plain")],
            deferred_runs=[],
            warnings=[],
            blocked_reasons=["x"],
        )
        r = build_manual_laptop_failure_operator_runorder(explicit_overwrite=True)
        self.assertEqual(r.get("runorder_status"), "blocked")
        self.assertIn("RUNORDER_SELECTION_NOT_ALLOWED", r.get("blocked_reasons") or [])

    def test_empty_selected_blocks(self) -> None:
        self._write_selection(
            selection_status="ready",
            selected_runs=[],
            deferred_runs=[],
            warnings=[],
            blocked_reasons=[],
        )
        r = build_manual_laptop_failure_operator_runorder(explicit_overwrite=True)
        self.assertEqual(r.get("runorder_status"), "blocked")
        self.assertIn("RUNORDER_SELECTED_RUNS_EMPTY", r.get("blocked_reasons") or [])

    def test_destructive_true_blocks(self) -> None:
        self._write_selection(
            selection_status="ready",
            selected_runs=[_run("s1", "case_plain", destructive=True)],
            deferred_runs=[],
            warnings=[],
            blocked_reasons=[],
        )
        r = build_manual_laptop_failure_operator_runorder(explicit_overwrite=True)
        self.assertEqual(r.get("runorder_status"), "blocked")
        self.assertTrue(any(d.get("reason") == "destructive_not_false" for d in (r.get("deferred_runs") or [])))

    def test_missing_abort_blocks(self) -> None:
        self._write_selection(
            selection_status="ready",
            selected_runs=[_run("s1", "case_plain", abort=[])],
            deferred_runs=[],
            warnings=[],
            blocked_reasons=[],
        )
        r = build_manual_laptop_failure_operator_runorder(explicit_overwrite=True)
        self.assertEqual(r.get("runorder_status"), "blocked")
        self.assertTrue(any(d.get("reason") == "missing_abort_conditions" for d in (r.get("deferred_runs") or [])))

    def test_grouping_order(self) -> None:
        # Erwartung: low vor medium (risk_rank), dann rollback, dann media — siehe _runorder_sort_key
        self._write_selection(
            selection_status="ready",
            selected_runs=[
                _run("s_media", "removed_usb_target", risk="low"),
                _run("s_rb", "case_plain", risk="low", rb=True),
                _run("s_med", "case_plain", risk="medium"),
                _run("s_plain", "case_plain", risk="low", rb=False),
            ],
            deferred_runs=[],
            warnings=[],
            blocked_reasons=[],
        )
        r = build_manual_laptop_failure_operator_runorder(explicit_overwrite=True)
        order = [x["session_id"] for x in r["ordered_runs"]]
        self.assertEqual(order, ["s_plain", "s_med", "s_rb", "s_media"])

    def test_atomic_no_tmp_after_write(self) -> None:
        self._write_selection(
            selection_status="ready",
            selected_runs=[_run("s1", "case_plain")],
            deferred_runs=[],
            warnings=[],
            blocked_reasons=[],
        )
        build_manual_laptop_failure_operator_runorder(explicit_overwrite=True)
        self.assertTrue(_RO.is_file())
        self.assertFalse((_HANDOFF / "laptop_failure_operator_runorder.json.tmp").exists())

    def test_no_subprocess_in_module(self) -> None:
        src = Path(__file__).resolve().parents[1] / "deploy" / "runner_manual_runtime_laptop_failure_operator_runorder.py"
        t = src.read_text(encoding="utf-8")
        self.assertNotIn("subprocess", t)
        self.assertNotIn("os.system", t)

    def test_route_only_calls_runorder(self) -> None:
        routes = Path(__file__).resolve().parents[1] / "deploy" / "routes.py"
        chunk = routes.read_text(encoding="utf-8")
        start = chunk.find("laptop-failure-operator-runorder")
        self.assertGreater(start, 0)
        block = chunk[start : start + 900]
        self.assertIn("build_manual_laptop_failure_operator_runorder", block)
        self.assertNotIn("execute_deploy", block)
        self.assertNotIn("execute_deploy_write", block)


if __name__ == "__main__":
    unittest.main()
