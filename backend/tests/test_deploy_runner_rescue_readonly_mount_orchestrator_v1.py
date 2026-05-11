from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_rescue_readonly_mount_orchestrator import (
    build_readonly_mount_plan,
    build_readonly_mount_result,
    execute_readonly_mount_validation,
)

_REPO = Path(__file__).resolve().parents[2]
_H = _REPO / "docs/evidence/runtime-results/handoff"
_PLAN = _H / "readonly_mount_plan.json"
_RES = _H / "readonly_mount_result.json"
_DISC = _H / "rescue_storage_discovery_result.json"


class DeployRunnerRescueReadonlyMountOrchestratorV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _H.mkdir(parents=True, exist_ok=True)
        self._backs = {p: p.read_bytes() if p.exists() else None for p in (_PLAN, _RES, _DISC)}
        for p in (_PLAN, _RES, _DISC):
            p.unlink(missing_ok=True)

    def tearDown(self) -> None:
        for p, bak in self._backs.items():
            if bak is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(bak)

    def test_rw_mount_blocked(self) -> None:
        _PLAN.write_text(
            json.dumps(
                {
                    "planned_operations": [
                        {"mountpoint": "build/rescue/runtime-mounts/x", "read_only": False, "filesystem": "ext4"}
                    ]
                }
            ),
            encoding="utf-8",
        )
        r = execute_readonly_mount_validation(explicit_overwrite=True, explicit_execute_readonly_mount=True)
        self.assertEqual(r.get("readonly_mount_result_status"), "blocked")

    def test_readonly_ok(self) -> None:
        _DISC.write_text(
            json.dumps({"lsblk_rows": [{"name": "sda1", "fstype": "ext4", "uuid": "u1"}]}),
            encoding="utf-8",
        )
        build_readonly_mount_plan(explicit_overwrite=True)
        r = execute_readonly_mount_validation(explicit_overwrite=True, explicit_execute_readonly_mount=True)
        self.assertEqual(r.get("readonly_mount_result_status"), "ok")
