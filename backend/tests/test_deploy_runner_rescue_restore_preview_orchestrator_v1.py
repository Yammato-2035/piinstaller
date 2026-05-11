from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_rescue_restore_preview_orchestrator import (
    build_rescue_restore_preview_plan,
    build_rescue_restore_preview_result,
    execute_rescue_restore_preview,
)

_REPO = Path(__file__).resolve().parents[2]
_H = _REPO / "docs/evidence/runtime-results/handoff"
_PLAN = _H / "rescue_restore_preview_plan.json"
_RES = _H / "rescue_restore_preview_result.json"
_BKV = _H / "rescue_backup_verify_result.json"
_DISC = _H / "rescue_storage_discovery_result.json"
_EFI = _H / "rescue_efi_boot_analysis.json"


class DeployRunnerRescueRestorePreviewOrchestratorV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _H.mkdir(parents=True, exist_ok=True)
        self._backs = {p: p.read_bytes() if p.exists() else None for p in (_PLAN, _RES, _BKV, _DISC, _EFI)}
        for p in (_PLAN, _RES, _BKV, _DISC, _EFI):
            p.unlink(missing_ok=True)

    def tearDown(self) -> None:
        for p, bak in self._backs.items():
            if bak is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(bak)

    def test_preview_no_writes(self) -> None:
        _BKV.write_text(
            json.dumps(
                {
                    "evaluation": {"restore_preview_possible": True, "rescue_backup_verify_eval_status": "ok"},
                    "verify": {"files_checked": [{"path": "a.txt", "ok": True}], "sha256_chain_ok": True, "pending": False},
                }
            ),
            encoding="utf-8",
        )
        _DISC.write_text(
            json.dumps({"lsblk_rows": [{"name": "sda2", "fstype": "ext4", "mountpoint": "/"}]}),
            encoding="utf-8",
        )
        _EFI.write_text(
            json.dumps({"efi_present": True, "grub_configuration_hints": False, "fstab_problems_hint": False}),
            encoding="utf-8",
        )
        build_rescue_restore_preview_plan(explicit_overwrite=True)
        r = execute_rescue_restore_preview(
            explicit_overwrite=True,
            explicit_execute_restore_preview=True,
        )
        body = r.get("rescue_restore_preview_result") or {}
        self.assertFalse(body.get("writes_executed"))
        rr = build_rescue_restore_preview_result(explicit_overwrite=True)
        self.assertEqual(rr.get("rescue_restore_preview_result_status"), "ok")
