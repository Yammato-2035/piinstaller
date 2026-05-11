from __future__ import annotations

import json
import unittest
from pathlib import Path
from deploy.runner_manual_runtime_laptop_failure_run_selector import select_manual_laptop_failure_test_runs

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_RD = _HANDOFF / "failure_test_readiness.json"
_SESS = _HANDOFF / "failure_test_sessions.json"
_CHK = _HANDOFF / "failure_operator_checklists.json"
_SEL = _HANDOFF / "laptop_failure_run_selection.json"


def _base_session(
    *,
    sid: str,
    ft: str,
    destructive: bool = False,
    abort: list | None = None,
    evidence: list | None = None,
    rollback_required: bool = False,
    extra: dict | None = None,
) -> dict:
    s = {
        "session_id": sid,
        "failure_type": ft,
        "execution_mode": "manual_only",
        "destructive": destructive,
        "rollback_required": rollback_required,
        "abort_conditions": abort if abort is not None else ["stop_if_unclear"],
        "evidence_to_capture": evidence if evidence is not None else ["log"],
    }
    if extra:
        s.update(extra)
    return s


def _checklist(*, ft: str, risk: str = "low", destructive: bool = False) -> dict:
    return {
        "failure_type": ft,
        "risk_level": risk,
        "destructive": destructive,
        "abort_conditions": ["op_abort"],
        "required_evidence": ["log"],
    }


class DeployRunnerManualRuntimeLaptopFailureRunSelectorV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        for p in (_RD, _SESS, _CHK, _SEL):
            p.unlink(missing_ok=True)
        for tmp in _HANDOFF.glob("laptop_failure_run_selection.json.tmp"):
            tmp.unlink(missing_ok=True)

    def tearDown(self) -> None:
        self.setUp()

    def _write_inputs(
        self,
        *,
        readiness: str,
        sessions: list[dict],
        checklists: list[dict],
    ) -> None:
        _RD.write_text(json.dumps({"readiness_status": readiness}), encoding="utf-8")
        _SESS.write_text(json.dumps({"test_sessions": sessions, "warnings": []}), encoding="utf-8")
        _CHK.write_text(json.dumps({"checklists": checklists, "warnings": []}), encoding="utf-8")

    def test_ready_produces_selection(self) -> None:
        ft = "sha256_mismatch"
        self._write_inputs(
            readiness="ready",
            sessions=[_base_session(sid="s1", ft=ft)],
            checklists=[_checklist(ft=ft, risk="low")],
        )
        r = select_manual_laptop_failure_test_runs(explicit_overwrite=True)
        self.assertEqual(r.get("selection_status"), "ready")
        self.assertEqual(len(r.get("selected_runs") or []), 1)
        self.assertEqual(r["selected_runs"][0]["session_id"], "s1")
        doc = json.loads(_SEL.read_text(encoding="utf-8"))
        self.assertEqual(doc["selection_status"], "ready")
        self.assertFalse((_HANDOFF / "laptop_failure_run_selection.json.tmp").exists())

    def test_review_required_produces_selection_with_warning(self) -> None:
        ft = "sha256_mismatch"
        self._write_inputs(
            readiness="review_required",
            sessions=[_base_session(sid="s1", ft=ft)],
            checklists=[_checklist(ft=ft)],
        )
        r = select_manual_laptop_failure_test_runs(explicit_overwrite=True)
        self.assertEqual(r.get("selection_status"), "review_required")
        self.assertIn("upstream_readiness_review_required", r.get("warnings") or [])

    def test_blocked_readiness_blocks(self) -> None:
        ft = "sha256_mismatch"
        self._write_inputs(
            readiness="blocked",
            sessions=[_base_session(sid="s1", ft=ft)],
            checklists=[_checklist(ft=ft)],
        )
        r = select_manual_laptop_failure_test_runs(explicit_overwrite=True)
        self.assertEqual(r.get("selection_status"), "blocked")
        self.assertIn("RUN_SELECT_READINESS_NOT_ALLOWED", r.get("blocked_reasons") or [])

    def test_destructive_true_defers_run(self) -> None:
        ft = "sha256_mismatch"
        self._write_inputs(
            readiness="ready",
            sessions=[_base_session(sid="s1", ft=ft, destructive=True)],
            checklists=[_checklist(ft=ft)],
        )
        r = select_manual_laptop_failure_test_runs(explicit_overwrite=True)
        self.assertEqual(r.get("selection_status"), "blocked")
        self.assertTrue(any("destructive_not_false" in str(d) for d in (r.get("deferred_runs") or [])))

    def test_missing_abort_conditions_defers_run(self) -> None:
        ft = "sha256_mismatch"
        self._write_inputs(
            readiness="ready",
            sessions=[_base_session(sid="s1", ft=ft, abort=[])],
            checklists=[_checklist(ft=ft)],
        )
        r = select_manual_laptop_failure_test_runs(explicit_overwrite=True)
        self.assertEqual(r.get("selection_status"), "blocked")
        self.assertTrue(any(d.get("reason") == "missing_abort_conditions" for d in (r.get("deferred_runs") or [])))

    def test_productive_marker_defers_run(self) -> None:
        ft = "sha256_mismatch"
        self._write_inputs(
            readiness="ready",
            sessions=[_base_session(sid="s1", ft=ft, extra={"notes": "touch /dev/sda only in prod"})],
            checklists=[_checklist(ft=ft)],
        )
        r = select_manual_laptop_failure_test_runs(explicit_overwrite=True)
        self.assertEqual(r.get("selection_status"), "blocked")
        dr = r.get("deferred_runs") or []
        self.assertTrue(any("productive_or_internal_marker" in str(d.get("reason", "")) for d in dr))

    def test_priority_low_before_medium(self) -> None:
        ft_low = "case_low"
        ft_med = "case_med"
        self._write_inputs(
            readiness="ready",
            sessions=[
                _base_session(sid="s_med", ft=ft_med),
                _base_session(sid="s_low", ft=ft_low),
            ],
            checklists=[
                _checklist(ft=ft_low, risk="low"),
                _checklist(ft=ft_med, risk="medium"),
            ],
        )
        r = select_manual_laptop_failure_test_runs(explicit_overwrite=True)
        self.assertEqual(r.get("selection_status"), "ready")
        sel = r.get("selected_runs") or []
        self.assertEqual(len(sel), 2)
        self.assertEqual(sel[0]["failure_type"], ft_low)
        self.assertEqual(sel[1]["failure_type"], ft_med)

    def test_atomic_write_leaves_no_tmp(self) -> None:
        ft = "sha256_mismatch"
        self._write_inputs(
            readiness="ready",
            sessions=[_base_session(sid="s1", ft=ft)],
            checklists=[_checklist(ft=ft)],
        )
        select_manual_laptop_failure_test_runs(explicit_overwrite=True)
        self.assertTrue(_SEL.is_file())
        self.assertFalse((_HANDOFF / "laptop_failure_run_selection.json.tmp").exists())

    def test_no_forbidden_subprocess_in_module_source(self) -> None:
        src = Path(__file__).resolve().parents[1] / "deploy" / "runner_manual_runtime_laptop_failure_run_selector.py"
        text = src.read_text(encoding="utf-8")
        self.assertNotIn("subprocess", text)
        self.assertNotIn("os.system", text)

    def test_route_only_calls_selector(self) -> None:
        routes = Path(__file__).resolve().parents[1] / "deploy" / "routes.py"
        chunk = routes.read_text(encoding="utf-8")
        start = chunk.find("laptop-failure-run-selection")
        self.assertGreater(start, 0)
        block = chunk[start : start + 800]
        self.assertIn("select_manual_laptop_failure_test_runs", block)
        self.assertNotIn("execute_deploy", block)
        self.assertNotIn("execute_deploy_write", block)


if __name__ == "__main__":
    unittest.main()
