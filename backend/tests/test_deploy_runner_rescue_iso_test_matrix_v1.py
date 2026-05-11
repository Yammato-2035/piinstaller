from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_rescue_iso_test_matrix import build_rescue_iso_test_matrix

_REPO = Path(__file__).resolve().parents[2]
_OUT = _REPO / "docs/evidence/runtime-results/handoff/rescue_iso_test_matrix.json"


class DeployRunnerRescueIsoTestMatrixV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _OUT.parent.mkdir(parents=True, exist_ok=True)
        self._bak = _OUT.read_bytes() if _OUT.exists() else None
        _OUT.unlink(missing_ok=True)

    def tearDown(self) -> None:
        if self._bak is None:
            _OUT.unlink(missing_ok=True)
        else:
            _OUT.write_bytes(self._bak)

    def test_vm_and_laptop_sections(self) -> None:
        res = build_rescue_iso_test_matrix(explicit_overwrite=True)
        self.assertEqual(res.get("rescue_iso_test_matrix_status"), "ok")
        body = res.get("rescue_iso_test_matrix") or {}
        self.assertIn("vm", body)
        self.assertIn("laptop", body)
        self.assertIn("bios_boot", body["vm"])
        self.assertIn("internal_nvme_detected", body["laptop"])
        parsed = json.loads(_OUT.read_text(encoding="utf-8"))
        self.assertIn("later", parsed)
