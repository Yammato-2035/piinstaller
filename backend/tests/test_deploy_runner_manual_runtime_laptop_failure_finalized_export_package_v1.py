from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from deploy.routes_source_aggregate import extract_deploy_route_block
from deploy.runner_manual_runtime_laptop_failure_finalized_export_package import (
    build_manual_laptop_failure_finalized_export_package,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_FILES = [
    "laptop_failure_final_acceptance.json",
    "laptop_failure_final_snapshot.json",
    "laptop_failure_evidence_timeline.json",
    "laptop_failure_final_export_package.json",
    "laptop_failure_final_report.json",
    "laptop_failure_test_summary.json",
    "laptop_failure_execution_log_validation.json",
    "laptop_failure_execution_log.json",
]
_OUT = _HANDOFF / "laptop_failure_finalized_export_package.json"


def _write(path: Path, body: dict) -> str:
    raw = json.dumps(body, indent=2, sort_keys=True).encode("utf-8")
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


class DeployRunnerManualRuntimeLaptopFailureFinalizedExportPackageV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        for name in _FILES:
            (_HANDOFF / name).unlink(missing_ok=True)
        _OUT.unlink(missing_ok=True)
        for tmp in _HANDOFF.glob("laptop_failure_finalized_export_package.json.tmp"):
            tmp.unlink(missing_ok=True)

    def tearDown(self) -> None:
        self.setUp()

    def _write_inputs(self, acceptance_status: str) -> dict[str, str]:
        shas: dict[str, str] = {}
        shas["docs/evidence/runtime-results/handoff/laptop_failure_final_acceptance.json"] = _write(
            _HANDOFF / "laptop_failure_final_acceptance.json",
            {"acceptance_status": acceptance_status},
        )
        shas["docs/evidence/runtime-results/handoff/laptop_failure_final_snapshot.json"] = _write(
            _HANDOFF / "laptop_failure_final_snapshot.json", {"snapshot_status": "ok"}
        )
        shas["docs/evidence/runtime-results/handoff/laptop_failure_evidence_timeline.json"] = _write(
            _HANDOFF / "laptop_failure_evidence_timeline.json", {"timeline_status": "ok", "events": [{}]}
        )
        shas["docs/evidence/runtime-results/handoff/laptop_failure_final_export_package.json"] = _write(
            _HANDOFF / "laptop_failure_final_export_package.json", {"export_status": "ok"}
        )
        shas["docs/evidence/runtime-results/handoff/laptop_failure_final_report.json"] = _write(
            _HANDOFF / "laptop_failure_final_report.json", {"report_status": "ok"}
        )
        shas["docs/evidence/runtime-results/handoff/laptop_failure_test_summary.json"] = _write(
            _HANDOFF / "laptop_failure_test_summary.json", {"summary_status": "ok"}
        )
        shas["docs/evidence/runtime-results/handoff/laptop_failure_execution_log_validation.json"] = _write(
            _HANDOFF / "laptop_failure_execution_log_validation.json", {"validation_status": "ok"}
        )
        shas["docs/evidence/runtime-results/handoff/laptop_failure_execution_log.json"] = _write(
            _HANDOFF / "laptop_failure_execution_log.json", {"ordered_runs": []}
        )
        return shas

    def test_ok_export(self) -> None:
        expected = self._write_inputs("accepted")
        res = build_manual_laptop_failure_finalized_export_package(explicit_overwrite=True)
        self.assertEqual(res.get("export_status"), "ok")
        self.assertEqual(res.get("file_count"), 8)
        self.assertEqual(res.get("sha256"), expected)

    def test_review_required_export(self) -> None:
        self._write_inputs("review_required")
        res = build_manual_laptop_failure_finalized_export_package(explicit_overwrite=True)
        self.assertEqual(res.get("export_status"), "review_required")

    def test_blocked_export(self) -> None:
        self._write_inputs("blocked")
        res = build_manual_laptop_failure_finalized_export_package(explicit_overwrite=True)
        self.assertEqual(res.get("export_status"), "blocked")

    def test_missing_file_blocked(self) -> None:
        self._write_inputs("accepted")
        (_HANDOFF / "laptop_failure_execution_log.json").unlink(missing_ok=True)
        res = build_manual_laptop_failure_finalized_export_package(explicit_overwrite=True)
        self.assertEqual(res.get("export_status"), "blocked")

    def test_overwrite_blockiert(self) -> None:
        self._write_inputs("accepted")
        first = build_manual_laptop_failure_finalized_export_package(explicit_overwrite=True)
        self.assertEqual(first.get("export_status"), "ok")
        second = build_manual_laptop_failure_finalized_export_package(explicit_overwrite=False)
        self.assertEqual(second.get("export_status"), "blocked")
        self.assertIn("FINALIZED_EXPORT_EXISTS_NO_OVERWRITE", second.get("blocked_reasons") or [])

    def test_atomisches_schreiben(self) -> None:
        self._write_inputs("accepted")
        build_manual_laptop_failure_finalized_export_package(explicit_overwrite=True)
        self.assertTrue(_OUT.is_file())
        self.assertFalse((_HANDOFF / "laptop_failure_finalized_export_package.json.tmp").exists())

    def test_keine_verbotenen_systemcalls(self) -> None:
        src = Path(__file__).resolve().parents[1] / "deploy" / "runner_manual_runtime_laptop_failure_finalized_export_package.py"
        t = src.read_text(encoding="utf-8")
        for bad in ("subprocess", "os.system", "mkfs", "dd ", "wipefs", "mount", "umount", "restore"):
            self.assertNotIn(bad, t)

    def test_keine_verbotenen_unterrouten(self) -> None:
        block = extract_deploy_route_block("laptop-failure-finalized-export-package")
        self.assertGreater(len(block), 0)
        for bad in ("execute", "apply", "install", "delete", "release"):
            self.assertNotIn(bad, block)


if __name__ == "__main__":
    unittest.main()
