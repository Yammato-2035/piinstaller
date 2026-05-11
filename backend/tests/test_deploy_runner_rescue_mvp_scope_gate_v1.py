from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_rescue_mvp_scope_gate import build_rescue_mvp_scope_gate
from deploy.runner_rescue_stick_component_inventory import build_rescue_stick_component_inventory

_REPO = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO / "docs/evidence/runtime-results/handoff"
_INV = _HANDOFF / "rescue_stick_component_inventory.json"
_OUT = _HANDOFF / "rescue_mvp_scope_gate.json"


class DeployRunnerRescueMvpScopeGateV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        self._inv_bak = _INV.read_bytes() if _INV.exists() else None
        self._out_bak = _OUT.read_bytes() if _OUT.exists() else None
        _OUT.unlink(missing_ok=True)

    def tearDown(self) -> None:
        for p, bak in ((_INV, self._inv_bak), (_OUT, self._out_bak)):
            if bak is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(bak)

    def test_ok_with_default_inventory(self) -> None:
        build_rescue_stick_component_inventory(explicit_overwrite=True)
        res = build_rescue_mvp_scope_gate(explicit_overwrite=True)
        self.assertEqual(res.get("rescue_mvp_scope_gate_status"), "ok")
        body = res.get("rescue_mvp_scope_gate") or {}
        self.assertTrue(body.get("forbidden_auto_operations_absent"))
        ex = body.get("mvp_excludes") or []
        self.assertIn("automatic_restore", ex)
        self.assertIn("automatic_bootloader_fix", ex)

    def test_blocked_when_forbidden_in_mvp(self) -> None:
        rows = [
            {
                "component": "evil",
                "component_id": "automatic_restore_execute",
                "status": "existing",
                "risk": "high",
                "required_for_mvp": True,
                "notes": [],
            }
        ]
        _INV.write_text(
            json.dumps({"components": rows, "rescue_stick_component_inventory_schema_version": 1}),
            encoding="utf-8",
        )
        res = build_rescue_mvp_scope_gate(explicit_overwrite=True)
        self.assertEqual(res.get("rescue_mvp_scope_gate_status"), "blocked")
