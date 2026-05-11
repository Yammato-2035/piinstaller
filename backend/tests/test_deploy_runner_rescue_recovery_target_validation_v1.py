from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_rescue_recovery_target_validation import (
    build_rescue_recovery_target_validation_plan,
    build_rescue_recovery_target_validation_result,
    execute_rescue_recovery_target_validation,
)

_REPO = Path(__file__).resolve().parents[2]
_H = _REPO / "docs/evidence/runtime-results/handoff"
_PLAN = _H / "rescue_recovery_target_validation_plan.json"
_RES = _H / "rescue_recovery_target_validation_result.json"
_MNT = _H / "readonly_mount_result.json"
_DISC = _H / "rescue_storage_discovery_result.json"


class DeployRunnerRescueRecoveryTargetValidationV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _H.mkdir(parents=True, exist_ok=True)
        self._backs = {p: p.read_bytes() if p.exists() else None for p in (_PLAN, _RES, _MNT, _DISC)}
        for p in (_PLAN, _RES, _MNT, _DISC):
            p.unlink(missing_ok=True)

    def tearDown(self) -> None:
        for p, bak in self._backs.items():
            if bak is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(bak)

    def _seed_ro_mount(self) -> None:
        _MNT.write_text(
            json.dumps({"evaluation": {"readonly_mount_eval_status": "ok", "readonly_enforced": True}}),
            encoding="utf-8",
        )

    def _seed_disc(self, *, uuid_conflict: bool = False) -> None:
        cls = {"flags": {}, "row_count": 1, "uuid_conflicts": ["dup"]} if uuid_conflict else {"flags": {}, "row_count": 1, "uuid_conflicts": []}
        _DISC.write_text(json.dumps({"classification": cls, "lsblk_rows": []}), encoding="utf-8")

    def test_wrong_internal_target_blocked(self) -> None:
        self._seed_ro_mount()
        self._seed_disc()
        build_rescue_recovery_target_validation_plan(
            explicit_overwrite=True,
            proposed_recovery_target="/home/user",
        )
        r = execute_rescue_recovery_target_validation(
            explicit_overwrite=True,
            explicit_execute_recovery_target_validation=True,
        )
        self.assertEqual(r.get("rescue_recovery_target_validation_result_status"), "blocked")

    def test_uuid_conflict_review(self) -> None:
        self._seed_ro_mount()
        self._seed_disc(uuid_conflict=True)
        build_rescue_recovery_target_validation_plan(
            explicit_overwrite=True,
            proposed_recovery_target="build/rescue/backup-verify-lab",
        )
        r = execute_rescue_recovery_target_validation(
            explicit_overwrite=True,
            explicit_execute_recovery_target_validation=True,
        )
        self.assertEqual(r.get("rescue_recovery_target_validation_result_status"), "review_required")
