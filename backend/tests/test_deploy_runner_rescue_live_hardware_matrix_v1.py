from __future__ import annotations

import unittest
from pathlib import Path

from deploy.runner_rescue_live_hardware_matrix import build_rescue_live_hardware_matrix

_REPO = Path(__file__).resolve().parents[2]
_OUT = _REPO / "docs/evidence/runtime-results/handoff/rescue_live_hardware_matrix.json"


class DeployRunnerRescueLiveHardwareMatrixV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _OUT.parent.mkdir(parents=True, exist_ok=True)
        self._bak = _OUT.read_bytes() if _OUT.exists() else None
        _OUT.unlink(missing_ok=True)

    def tearDown(self) -> None:
        if self._bak is None:
            _OUT.unlink(missing_ok=True)
        else:
            _OUT.write_bytes(self._bak)

    def test_matrix_contains_asus_nvme(self) -> None:
        r = build_rescue_live_hardware_matrix(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_live_hardware_matrix_status"), "ok")
        tested = (r.get("rescue_live_hardware_matrix") or {}).get("tested") or {}
        self.assertTrue(tested.get("nvme"))
        self.assertTrue(tested.get("efi"))
