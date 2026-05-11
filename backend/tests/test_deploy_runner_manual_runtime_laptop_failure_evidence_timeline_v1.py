from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from deploy.runner_manual_runtime_laptop_failure_evidence_timeline import (
    build_manual_laptop_failure_evidence_timeline,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_EXPORT = _HANDOFF / "laptop_failure_final_export_package.json"
_REPORT = _HANDOFF / "laptop_failure_final_report.json"
_SUMMARY = _HANDOFF / "laptop_failure_test_summary.json"
_VALIDATION = _HANDOFF / "laptop_failure_execution_log_validation.json"
_EXEC_LOG = _HANDOFF / "laptop_failure_execution_log.json"
_OUT = _HANDOFF / "laptop_failure_evidence_timeline.json"


def _write(path: Path, body: dict) -> str:
    raw = json.dumps(body, indent=2, sort_keys=True).encode("utf-8")
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


class DeployRunnerManualRuntimeLaptopFailureEvidenceTimelineV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        for p in (_EXPORT, _REPORT, _SUMMARY, _VALIDATION, _EXEC_LOG, _OUT):
            p.unlink(missing_ok=True)
        for tmp in _HANDOFF.glob("laptop_failure_evidence_timeline.json.tmp"):
            tmp.unlink(missing_ok=True)

    def tearDown(self) -> None:
        self.setUp()

    def _write_inputs(self, export_status: str) -> dict[str, str]:
        hashes: dict[str, str] = {}
        hashes["docs/evidence/runtime-results/handoff/laptop_failure_final_export_package.json"] = _write(
            _EXPORT, {"export_status": export_status, "generated_at": "2026-05-09T10:10:00Z"}
        )
        hashes["docs/evidence/runtime-results/handoff/laptop_failure_final_report.json"] = _write(
            _REPORT, {"report_status": "ok", "generated_at": "2026-05-09T10:00:00Z"}
        )
        hashes["docs/evidence/runtime-results/handoff/laptop_failure_test_summary.json"] = _write(
            _SUMMARY, {"summary_status": "ok", "generated_at": "2026-05-09T09:50:00Z"}
        )
        hashes["docs/evidence/runtime-results/handoff/laptop_failure_execution_log_validation.json"] = _write(
            _VALIDATION, {"validation_status": "ok", "generated_at": "2026-05-09T09:40:00Z"}
        )
        hashes["docs/evidence/runtime-results/handoff/laptop_failure_execution_log.json"] = _write(
            _EXEC_LOG, {"generated_at": "2026-05-09T09:30:00Z", "ordered_runs": []}
        )
        return hashes

    def test_ok_status_and_hashes(self) -> None:
        expected = self._write_inputs("ok")
        res = build_manual_laptop_failure_evidence_timeline(explicit_overwrite=True)
        self.assertEqual(res.get("timeline_status"), "ok")
        events = res.get("events") or []
        self.assertEqual(len(events), 5)
        by_path = {e["path"]: e["sha256"] for e in events}
        self.assertEqual(by_path, expected)

    def test_review_required_status(self) -> None:
        self._write_inputs("review_required")
        res = build_manual_laptop_failure_evidence_timeline(explicit_overwrite=True)
        self.assertEqual(res.get("timeline_status"), "review_required")

    def test_blocked_status(self) -> None:
        self._write_inputs("blocked")
        res = build_manual_laptop_failure_evidence_timeline(explicit_overwrite=True)
        self.assertEqual(res.get("timeline_status"), "blocked")

    def test_chronological_sort(self) -> None:
        self._write_inputs("ok")
        res = build_manual_laptop_failure_evidence_timeline(explicit_overwrite=True)
        ts = [e["timestamp"] for e in (res.get("events") or [])]
        self.assertEqual(ts, sorted(ts))

    def test_overwrite_blockiert(self) -> None:
        self._write_inputs("ok")
        first = build_manual_laptop_failure_evidence_timeline(explicit_overwrite=True)
        self.assertEqual(first.get("timeline_status"), "ok")
        second = build_manual_laptop_failure_evidence_timeline(explicit_overwrite=False)
        self.assertEqual(second.get("timeline_status"), "blocked")
        self.assertIn("EVIDENCE_TIMELINE_EXISTS_NO_OVERWRITE", second.get("blocked_reasons") or [])

    def test_atomisches_schreiben(self) -> None:
        self._write_inputs("ok")
        build_manual_laptop_failure_evidence_timeline(explicit_overwrite=True)
        self.assertTrue(_OUT.is_file())
        self.assertFalse((_HANDOFF / "laptop_failure_evidence_timeline.json.tmp").exists())

    def test_keine_verbotenen_systemcalls(self) -> None:
        src = Path(__file__).resolve().parents[1] / "deploy" / "runner_manual_runtime_laptop_failure_evidence_timeline.py"
        text = src.read_text(encoding="utf-8")
        self.assertNotIn("subprocess", text)
        self.assertNotIn("os.system", text)

    def test_keine_verbotenen_unterrouten(self) -> None:
        routes = Path(__file__).resolve().parents[1] / "deploy" / "routes.py"
        chunk = routes.read_text(encoding="utf-8")
        start = chunk.find("laptop-failure-evidence-timeline")
        self.assertGreater(start, 0)
        block = chunk[start : start + 1000]
        self.assertIn("build_manual_laptop_failure_evidence_timeline", block)
        self.assertNotIn("execute_deploy", block)
        self.assertNotIn("execute_deploy_write", block)


if __name__ == "__main__":
    unittest.main()
