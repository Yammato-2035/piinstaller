from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest import mock

from deploy.runner_rescue_vm_test_orchestrator import build_rescue_vm_test_plan, execute_rescue_vm_boot_validation

_REPO = Path(__file__).resolve().parents[2]
_H = _REPO / "docs/evidence/runtime-results/handoff"
_PLAN = _H / "rescue_vm_test_plan.json"
_RES = _H / "rescue_vm_test_result.json"
_ISO = _REPO / "build/rescue/output/test-vm.iso"


class DeployRunnerRescueVmTestOrchestratorV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _H.mkdir(parents=True, exist_ok=True)
        self._p_bak = _PLAN.read_bytes() if _PLAN.exists() else None
        self._r_bak = _RES.read_bytes() if _RES.exists() else None
        _PLAN.unlink(missing_ok=True)
        _RES.unlink(missing_ok=True)
        _ISO.parent.mkdir(parents=True, exist_ok=True)
        self._iso_bak = _ISO.read_bytes() if _ISO.exists() else None
        _ISO.write_bytes(b"x")

    def tearDown(self) -> None:
        for p, bak in ((_PLAN, self._p_bak), (_RES, self._r_bak)):
            if bak is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(bak)
        if self._iso_bak is None:
            _ISO.unlink(missing_ok=True)
        else:
            _ISO.write_bytes(self._iso_bak)

    def test_plan_contains_vm_and_laptop_constraints(self) -> None:
        r = build_rescue_vm_test_plan(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_vm_test_plan_status"), "ok")
        body = r.get("rescue_vm_test_plan") or {}
        self.assertIn("iso_path", body)
        self.assertEqual(body.get("constraints", {}).get("no_host_raw_disk"), True)

    def test_execute_blocked_without_flag(self) -> None:
        build_rescue_vm_test_plan(explicit_overwrite=True)
        r = execute_rescue_vm_boot_validation(explicit_overwrite=True, explicit_execute_vm_boot=False)
        self.assertEqual(r.get("rescue_vm_test_result_status"), "blocked")

    @mock.patch("deploy.runner_rescue_vm_test_orchestrator.shutil.which", return_value="/usr/bin/qemu-system-x86_64")
    @mock.patch("deploy.runner_rescue_vm_test_orchestrator.subprocess.run")
    def test_execute_ok_with_qemu(self, mock_run: mock.MagicMock, _which: mock.MagicMock) -> None:
        build_rescue_vm_test_plan(explicit_overwrite=True)
        mock_run.return_value = mock.MagicMock(returncode=0, stdout="", stderr="")
        r = execute_rescue_vm_boot_validation(explicit_overwrite=True, explicit_execute_vm_boot=True)
        self.assertEqual(r.get("rescue_vm_test_result_status"), "ok")
