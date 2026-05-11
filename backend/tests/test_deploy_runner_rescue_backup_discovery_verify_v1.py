from __future__ import annotations

import hashlib
import json
import shutil
import unittest
from pathlib import Path

from deploy.runner_rescue_backup_discovery_verify import (
    build_rescue_backup_discovery_plan,
    build_rescue_backup_verify_result,
    execute_rescue_backup_discovery,
    execute_rescue_backup_verify,
)

_REPO = Path(__file__).resolve().parents[2]
_H = _REPO / "docs/evidence/runtime-results/handoff"
_LAB = _REPO / "build/rescue/backup-verify-lab"
_PLAN = _H / "rescue_backup_discovery_plan.json"
_RES = _H / "rescue_backup_verify_result.json"


class DeployRunnerRescueBackupDiscoveryVerifyV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _H.mkdir(parents=True, exist_ok=True)
        _LAB.mkdir(parents=True, exist_ok=True)
        self._backs = {p: p.read_bytes() if p.exists() else None for p in (_PLAN, _RES)}
        for p in (_PLAN, _RES):
            p.unlink(missing_ok=True)

    def tearDown(self) -> None:
        for p, bak in self._backs.items():
            if bak is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(bak)
        shutil.rmtree(_LAB, ignore_errors=True)

    def _write_manifest(self, *, corrupt: bool = False) -> None:
        data_rel = "build/rescue/backup-verify-lab/data.txt"
        p = _REPO / "build/rescue/backup-verify-lab/data.txt"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("hello-backup", encoding="utf-8")
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        if corrupt:
            h = "0" * 64
        man = {"backup_version": "1.0", "files": [{"path": "data.txt", "sha256": h}]}
        (_LAB / "backup_manifest.json").write_text(json.dumps(man), encoding="utf-8")

    def test_sha256_mismatch_blocked(self) -> None:
        build_rescue_backup_discovery_plan(explicit_overwrite=True, backup_scan_root="build/rescue/backup-verify-lab")
        self._write_manifest(corrupt=True)
        execute_rescue_backup_discovery(
            explicit_overwrite=True,
            explicit_execute_backup_discovery=True,
        )
        execute_rescue_backup_verify(
            explicit_overwrite=True,
            explicit_execute_backup_verify=True,
        )
        r = build_rescue_backup_verify_result(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_backup_verify_result_status"), "blocked")

    def test_verify_ok(self) -> None:
        build_rescue_backup_discovery_plan(explicit_overwrite=True, backup_scan_root="build/rescue/backup-verify-lab")
        self._write_manifest(corrupt=False)
        execute_rescue_backup_discovery(
            explicit_overwrite=True,
            explicit_execute_backup_discovery=True,
        )
        execute_rescue_backup_verify(
            explicit_overwrite=True,
            explicit_execute_backup_verify=True,
        )
        r = build_rescue_backup_verify_result(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_backup_verify_result_status"), "ok")
        ev = (r.get("rescue_backup_verify_result") or {}).get("evaluation") or {}
        self.assertTrue(ev.get("restore_preview_possible"))
