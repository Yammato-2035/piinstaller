from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest import mock

from deploy.runner_rescue_iso_build_execution import (
    build_rescue_iso_build_precheck,
    build_rescue_iso_build_result,
    execute_rescue_iso_build,
)

_REPO = Path(__file__).resolve().parents[2]
_H = _REPO / "docs/evidence/runtime-results/handoff"
_PRE = _H / "rescue_iso_build_precheck.json"
_RES = _H / "rescue_iso_build_result.json"
_OUT = _REPO / "build/rescue/output"
_LOG = _REPO / "build/rescue/logs"


class DeployRunnerRescueIsoBuildExecutionV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _H.mkdir(parents=True, exist_ok=True)
        self._pre_bak = _PRE.read_bytes() if _PRE.exists() else None
        self._res_bak = _RES.read_bytes() if _RES.exists() else None
        _PRE.unlink(missing_ok=True)
        _RES.unlink(missing_ok=True)
        _OUT.mkdir(parents=True, exist_ok=True)
        for p in _OUT.glob("*.iso"):
            p.unlink()
        self._iso = _OUT / "setuphelfer-rescue-test.iso"
        self._iso.unlink(missing_ok=True)

    def tearDown(self) -> None:
        for p, bak in ((_PRE, self._pre_bak), (_RES, self._res_bak)):
            if bak is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(bak)
        self._iso.unlink(missing_ok=True)

    def test_precheck_ok_with_low_threshold(self) -> None:
        r = build_rescue_iso_build_precheck(explicit_overwrite=True, min_free_disk_bytes=1)
        self.assertEqual(r.get("rescue_iso_build_precheck_status"), "ok")

    def test_execute_requires_both_flags(self) -> None:
        r = execute_rescue_iso_build(
            explicit_overwrite=True,
            explicit_execute_iso_build=False,
            explicit_rescue_build_approved=True,
        )
        self.assertEqual(r.get("rescue_iso_build_result_status"), "blocked")
        r2 = execute_rescue_iso_build(
            explicit_overwrite=True,
            explicit_execute_iso_build=True,
            explicit_rescue_build_approved=False,
        )
        self.assertEqual(r2.get("rescue_iso_build_result_status"), "blocked")

    def test_result_detects_forbidden_in_logs(self) -> None:
        _LOG.mkdir(parents=True, exist_ok=True)
        log_rel = "build/rescue/logs/fake-forbidden.log"
        (_REPO / log_rel).write_text("simulated dd if=/dev/zero of=/dev/sdb\n", encoding="utf-8")
        r = build_rescue_iso_build_result(
            explicit_overwrite=True,
            subprocess_exit_code=0,
            subprocess_log_path=log_rel,
            forbidden_hits=[],
        )
        self.assertEqual(r.get("rescue_iso_build_result_status"), "blocked")
        (_REPO / log_rel).unlink(missing_ok=True)

    @mock.patch("deploy.runner_rescue_iso_build_execution.subprocess.run")
    def test_execute_success_writes_iso(self, mock_run: mock.MagicMock) -> None:
        mock_run.return_value = mock.MagicMock(returncode=0, stdout="ok\n", stderr="")
        self._iso.write_bytes(b"FAKEISO")
        r = execute_rescue_iso_build(
            explicit_overwrite=True,
            explicit_execute_iso_build=True,
            explicit_rescue_build_approved=True,
            build_timeout_seconds=120,
        )
        self.assertEqual(r.get("rescue_iso_build_result_status"), "ok")
        self.assertTrue((r.get("rescue_iso_build_result") or {}).get("build_success"))
