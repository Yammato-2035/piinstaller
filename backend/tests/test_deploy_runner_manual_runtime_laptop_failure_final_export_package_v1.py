from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from deploy.runner_manual_runtime_laptop_failure_final_export_package import (
    build_manual_laptop_failure_final_export_package,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_FINAL_REPORT = _HANDOFF / "laptop_failure_final_report.json"
_SUMMARY = _HANDOFF / "laptop_failure_test_summary.json"
_VALIDATION = _HANDOFF / "laptop_failure_execution_log_validation.json"
_EXEC_LOG = _HANDOFF / "laptop_failure_execution_log.json"
_OUT = _HANDOFF / "laptop_failure_final_export_package.json"


def _write_json(path: Path, body: dict) -> bytes:
    raw = json.dumps(body, indent=2, sort_keys=True).encode("utf-8")
    path.write_bytes(raw)
    return raw


class DeployRunnerManualRuntimeLaptopFailureFinalExportPackageV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        for p in (_FINAL_REPORT, _SUMMARY, _VALIDATION, _EXEC_LOG, _OUT):
            p.unlink(missing_ok=True)
        for tmp in _HANDOFF.glob("laptop_failure_final_export_package.json.tmp"):
            tmp.unlink(missing_ok=True)

    def tearDown(self) -> None:
        self.setUp()

    def _write_inputs(self, report_status: str) -> dict[str, str]:
        hashes: dict[str, str] = {}
        hashes[str(_FINAL_REPORT)] = hashlib.sha256(
            _write_json(
                _FINAL_REPORT,
                {
                    "report_status": report_status,
                    "recommendation": "proceed" if report_status == "ok" else "blocked",
                },
            )
        ).hexdigest()
        hashes[str(_SUMMARY)] = hashlib.sha256(
            _write_json(_SUMMARY, {"summary_status": "ok", "total_runs": 1})
        ).hexdigest()
        hashes[str(_VALIDATION)] = hashlib.sha256(
            _write_json(_VALIDATION, {"validation_status": "ok", "run_validations": []})
        ).hexdigest()
        hashes[str(_EXEC_LOG)] = hashlib.sha256(
            _write_json(_EXEC_LOG, {"ordered_runs": []})
        ).hexdigest()
        return hashes

    def test_ok_status_and_hashes(self) -> None:
        expected = self._write_inputs("ok")
        res = build_manual_laptop_failure_final_export_package(explicit_overwrite=True)
        self.assertEqual(res.get("export_status"), "ok")
        by_path = {x["path"]: x["sha256"] for x in (res.get("included_files") or [])}
        self.assertEqual(
            by_path["docs/evidence/runtime-results/handoff/laptop_failure_final_report.json"],
            expected[str(_FINAL_REPORT)],
        )

    def test_review_required_status(self) -> None:
        self._write_inputs("review_required")
        res = build_manual_laptop_failure_final_export_package(explicit_overwrite=True)
        self.assertEqual(res.get("export_status"), "review_required")

    def test_blocked_status(self) -> None:
        self._write_inputs("blocked")
        res = build_manual_laptop_failure_final_export_package(explicit_overwrite=True)
        self.assertEqual(res.get("export_status"), "blocked")

    def test_overwrite_blockiert(self) -> None:
        self._write_inputs("ok")
        first = build_manual_laptop_failure_final_export_package(explicit_overwrite=True)
        self.assertEqual(first.get("export_status"), "ok")
        second = build_manual_laptop_failure_final_export_package(explicit_overwrite=False)
        self.assertEqual(second.get("export_status"), "blocked")
        self.assertIn("FINAL_EXPORT_EXISTS_NO_OVERWRITE", second.get("blocked_reasons") or [])

    def test_atomisches_schreiben(self) -> None:
        self._write_inputs("ok")
        build_manual_laptop_failure_final_export_package(explicit_overwrite=True)
        self.assertTrue(_OUT.is_file())
        self.assertFalse((_HANDOFF / "laptop_failure_final_export_package.json.tmp").exists())

    def test_keine_verbotenen_systemcalls(self) -> None:
        src = (
            Path(__file__).resolve().parents[1]
            / "deploy"
            / "runner_manual_runtime_laptop_failure_final_export_package.py"
        )
        text = src.read_text(encoding="utf-8")
        self.assertNotIn("subprocess", text)
        self.assertNotIn("os.system", text)

    def test_keine_verbotenen_unterrouten(self) -> None:
        routes = Path(__file__).resolve().parents[1] / "deploy" / "routes.py"
        chunk = routes.read_text(encoding="utf-8")
        start = chunk.find("laptop-failure-final-export-package")
        self.assertGreater(start, 0)
        block = chunk[start : start + 1000]
        self.assertIn("build_manual_laptop_failure_final_export_package", block)
        self.assertNotIn("execute_deploy", block)
        self.assertNotIn("execute_deploy_write", block)


if __name__ == "__main__":
    unittest.main()
