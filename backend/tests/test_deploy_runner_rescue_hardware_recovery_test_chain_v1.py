from __future__ import annotations

import unittest
from pathlib import Path

from deploy.runner_rescue_hardware_recovery_test_chain import build_rescue_hardware_recovery_test_chain

_REPO = Path(__file__).resolve().parents[2]
_OUT = _REPO / "docs/evidence/runtime-results/handoff/rescue_hardware_recovery_test_chain.json"


class DeployRunnerRescueHardwareRecoveryTestChainV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _OUT.parent.mkdir(parents=True, exist_ok=True)
        self._bak = _OUT.read_bytes() if _OUT.exists() else None
        _OUT.unlink(missing_ok=True)

    def tearDown(self) -> None:
        if self._bak is None:
            _OUT.unlink(missing_ok=True)
        else:
            _OUT.write_bytes(self._bak)

    def test_chain_has_nine_steps(self) -> None:
        r = build_rescue_hardware_recovery_test_chain(explicit_overwrite=True)
        body = r.get("rescue_hardware_recovery_test_chain") or {}
        steps = body.get("steps") or []
        self.assertEqual(len(steps), 9)
        self.assertIn("iso_boot", {s.get("id") for s in steps})
