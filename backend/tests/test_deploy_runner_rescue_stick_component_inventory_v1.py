from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_rescue_stick_component_inventory import build_rescue_stick_component_inventory

_REPO = Path(__file__).resolve().parents[2]
_OUT = _REPO / "docs/evidence/runtime-results/handoff/rescue_stick_component_inventory.json"


class DeployRunnerRescueStickComponentInventoryV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _OUT.parent.mkdir(parents=True, exist_ok=True)
        self._bak = _OUT.read_bytes() if _OUT.exists() else None
        _OUT.unlink(missing_ok=True)

    def tearDown(self) -> None:
        if self._bak is None:
            _OUT.unlink(missing_ok=True)
        else:
            _OUT.write_bytes(self._bak)

    def test_existing_and_missing_markers(self) -> None:
        res = build_rescue_stick_component_inventory(explicit_overwrite=True)
        self.assertEqual(res.get("rescue_stick_component_inventory_status"), "ok")
        body = res.get("rescue_stick_component_inventory") or {}
        rows = body.get("components") or []
        ids = {str(r.get("component_id")): r for r in rows if isinstance(r, dict)}
        self.assertEqual(ids.get("inspect", {}).get("status"), "existing")
        self.assertEqual(ids.get("verify", {}).get("status"), "existing")
        self.assertEqual(ids.get("debian_live_build_config", {}).get("status"), "missing")
        self.assertEqual(ids.get("iso_test_pipeline", {}).get("status"), "missing")
        parsed = json.loads(_OUT.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(parsed.get("components") or []), 10)
