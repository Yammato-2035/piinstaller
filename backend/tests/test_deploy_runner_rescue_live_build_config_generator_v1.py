from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_rescue_live_build_config_generator import build_rescue_live_build_config

_REPO = Path(__file__).resolve().parents[2]
_OUT = _REPO / "docs/evidence/runtime-results/handoff/rescue_live_build_config.json"


class DeployRunnerRescueLiveBuildConfigGeneratorV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _OUT.parent.mkdir(parents=True, exist_ok=True)
        self._bak = _OUT.read_bytes() if _OUT.exists() else None
        _OUT.unlink(missing_ok=True)

    def tearDown(self) -> None:
        if self._bak is None:
            _OUT.unlink(missing_ok=True)
        else:
            _OUT.write_bytes(self._bak)

    def test_amd64_debian_stable(self) -> None:
        res = build_rescue_live_build_config(explicit_overwrite=True)
        self.assertEqual(res.get("rescue_live_build_config_status"), "ok")
        body = res.get("rescue_live_build_config") or {}
        self.assertEqual(body.get("debian", {}).get("arch"), "amd64")
        self.assertEqual(body.get("execution_mode"), "config_only_no_build")
        self.assertTrue(body.get("readonly_rescue_mode"))
        parsed = json.loads(_OUT.read_text(encoding="utf-8"))
        self.assertIn("setuphelfer_services", parsed)
