from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_manual_runtime_laptop_failure_execution_log_template import (
    build_manual_laptop_failure_execution_log_template,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_RUNORDER = _HANDOFF / "laptop_failure_operator_runorder.json"
_OUT = _HANDOFF / "laptop_failure_execution_log.json"


def _ordered_run(
    run_id: str,
    ft: str,
    *,
    step: int = 1,
    mode: str = "manual_only",
    destructive: bool | None = None,
    abort: list | None = None,
    evidence: list | None = None,
) -> dict:
    run: dict[str, object] = {
        "session_id": run_id,
        "failure_type": ft,
        "operator_step_index": step,
        "execution_mode": mode,
        "abort_conditions": abort if abort is not None else ["abort_if_unsafe"],
        "evidence_to_capture": evidence if evidence is not None else ["operator_log"],
    }
    if destructive is not None:
        run["destructive"] = destructive
    return run


class DeployRunnerManualRuntimeLaptopFailureExecutionLogTemplateV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        for p in (_RUNORDER, _OUT):
            p.unlink(missing_ok=True)
        for tmp in _HANDOFF.glob("laptop_failure_execution_log.json.tmp"):
            tmp.unlink(missing_ok=True)

    def tearDown(self) -> None:
        self.setUp()

    def _write_runorder(self, **kwargs: object) -> None:
        _RUNORDER.write_text(json.dumps(kwargs, indent=2), encoding="utf-8")

    def test_template_erzeugbar(self) -> None:
        self._write_runorder(
            runorder_status="ready",
            ordered_runs=[_ordered_run("r1", "sha256_mismatch")],
            deferred_runs=[],
            warnings=[],
            blocked_reasons=[],
        )
        res = build_manual_laptop_failure_execution_log_template(explicit_overwrite=True)
        self.assertEqual(res.get("template_status"), "ok")
        self.assertTrue(_OUT.is_file())

    def test_alle_ordered_runs_enthalten(self) -> None:
        self._write_runorder(
            runorder_status="ready",
            ordered_runs=[_ordered_run("r1", "a", step=1), _ordered_run("r2", "b", step=2)],
            deferred_runs=[],
            warnings=[],
            blocked_reasons=[],
        )
        res = build_manual_laptop_failure_execution_log_template(explicit_overwrite=True)
        runs = res.get("ordered_runs") or []
        self.assertEqual(len(runs), 2)
        self.assertEqual([r["run_id"] for r in runs], ["r1", "r2"])

    def test_destructive_immer_false(self) -> None:
        self._write_runorder(
            runorder_status="ready",
            ordered_runs=[_ordered_run("r1", "a")],
            deferred_runs=[],
            warnings=[],
            blocked_reasons=[],
        )
        res = build_manual_laptop_failure_execution_log_template(explicit_overwrite=True)
        self.assertTrue(all(r.get("destructive") is False for r in (res.get("ordered_runs") or [])))

    def test_pre_post_state_vorhanden(self) -> None:
        self._write_runorder(
            runorder_status="ready",
            ordered_runs=[_ordered_run("r1", "a")],
            deferred_runs=[],
            warnings=[],
            blocked_reasons=[],
        )
        res = build_manual_laptop_failure_execution_log_template(explicit_overwrite=True)
        r0 = (res.get("ordered_runs") or [])[0]
        self.assertIn("pre_state", r0)
        self.assertIn("post_state", r0)
        self.assertIn("lsblk", r0["pre_state"])
        self.assertIn("findmnt", r0["post_state"])

    def test_evidence_collected_vorhanden(self) -> None:
        self._write_runorder(
            runorder_status="ready",
            ordered_runs=[_ordered_run("r1", "a")],
            deferred_runs=[],
            warnings=[],
            blocked_reasons=[],
        )
        res = build_manual_laptop_failure_execution_log_template(explicit_overwrite=True)
        self.assertIsInstance((res.get("ordered_runs") or [])[0].get("evidence_collected"), list)

    def test_abort_felder_vorhanden(self) -> None:
        self._write_runorder(
            runorder_status="ready",
            ordered_runs=[_ordered_run("r1", "a")],
            deferred_runs=[],
            warnings=[],
            blocked_reasons=[],
        )
        res = build_manual_laptop_failure_execution_log_template(explicit_overwrite=True)
        r0 = (res.get("ordered_runs") or [])[0]
        self.assertIn("abort_triggered", r0)
        self.assertIn("abort_reason", r0)

    def test_overwrite_blockiert(self) -> None:
        self._write_runorder(
            runorder_status="ready",
            ordered_runs=[_ordered_run("r1", "a")],
            deferred_runs=[],
            warnings=[],
            blocked_reasons=[],
        )
        first = build_manual_laptop_failure_execution_log_template(explicit_overwrite=True)
        self.assertEqual(first.get("template_status"), "ok")
        second = build_manual_laptop_failure_execution_log_template(explicit_overwrite=False)
        self.assertEqual(second.get("template_status"), "blocked")
        self.assertIn("EXEC_LOG_TEMPLATE_EXISTS_NO_OVERWRITE", second.get("blocked_reasons") or [])

    def test_atomisches_schreiben(self) -> None:
        self._write_runorder(
            runorder_status="ready",
            ordered_runs=[_ordered_run("r1", "a")],
            deferred_runs=[],
            warnings=[],
            blocked_reasons=[],
        )
        build_manual_laptop_failure_execution_log_template(explicit_overwrite=True)
        self.assertTrue(_OUT.is_file())
        self.assertFalse((_HANDOFF / "laptop_failure_execution_log.json.tmp").exists())

    def test_keine_verbotenen_systemcalls(self) -> None:
        src = (
            Path(__file__).resolve().parents[1]
            / "deploy"
            / "runner_manual_runtime_laptop_failure_execution_log_template.py"
        )
        text = src.read_text(encoding="utf-8")
        self.assertNotIn("subprocess", text)
        self.assertNotIn("os.system", text)

    def test_keine_verbotenen_unterrouten(self) -> None:
        routes = Path(__file__).resolve().parents[1] / "deploy" / "routes.py"
        chunk = routes.read_text(encoding="utf-8")
        start = chunk.find("laptop-failure-execution-log-template")
        self.assertGreater(start, 0)
        block = chunk[start : start + 1000]
        self.assertIn("build_manual_laptop_failure_execution_log_template", block)
        self.assertNotIn("execute_deploy", block)
        self.assertNotIn("execute_deploy_write", block)


if __name__ == "__main__":
    unittest.main()
