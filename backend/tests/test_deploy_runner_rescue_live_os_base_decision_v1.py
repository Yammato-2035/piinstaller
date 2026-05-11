from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_rescue_live_os_base_decision import build_rescue_live_os_base_decision

_REPO = Path(__file__).resolve().parents[2]
_OUT = _REPO / "docs/evidence/runtime-results/handoff/rescue_live_os_base_decision.json"


class DeployRunnerRescueLiveOsBaseDecisionV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _OUT.parent.mkdir(parents=True, exist_ok=True)
        self._bak = _OUT.read_bytes() if _OUT.exists() else None
        _OUT.unlink(missing_ok=True)

    def tearDown(self) -> None:
        if self._bak is None:
            _OUT.unlink(missing_ok=True)
        else:
            _OUT.write_bytes(self._bak)

    def test_debian_live_recommended_and_secure_boot_review(self) -> None:
        res = build_rescue_live_os_base_decision(explicit_overwrite=True)
        self.assertEqual(res.get("rescue_live_os_base_decision_status"), "ok")
        body = res.get("rescue_live_os_base_decision") or {}
        self.assertEqual(body.get("recommended_live_os_base"), "debian_live")
        ev = body.get("evaluation") or {}
        self.assertIn("alpine", ev)
        self.assertIn("archiso", ev)
        self.assertNotEqual(body.get("recommended_live_os_base"), "alpine")
        self.assertNotEqual(body.get("recommended_live_os_base"), "archiso")
        self.assertEqual(body.get("secure_boot_status"), "review_required")
        self.assertTrue(any("SECUREBOOT" in str(w) for w in (res.get("warnings") or [])))
        parsed = json.loads(_OUT.read_text(encoding="utf-8"))
        self.assertEqual(parsed.get("recommended_live_os_base"), "debian_live")

    def test_no_overwrite_without_flag(self) -> None:
        build_rescue_live_os_base_decision(explicit_overwrite=True)
        res = build_rescue_live_os_base_decision(explicit_overwrite=False)
        self.assertEqual(res.get("rescue_live_os_base_decision_status"), "blocked")
