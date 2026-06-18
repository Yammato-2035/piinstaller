"""RS-P2A WiFi runtime contract tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_backend))

from core.rescue_wifi_runtime_contract import classify_wifi_runtime_blockers, wifi_runtime_preflight_steps


class TestRescueWifiRuntimeContractV1(unittest.TestCase):
    def test_ensure_managed_in_steps(self):
        self.assertIn("ensure_managed", wifi_runtime_preflight_steps())

    def test_hdd_not_blocked(self):
        out = classify_wifi_runtime_blockers(
            wifi_status={"blocks_local_hdd_backup": False, "blocks_cloud_backup": True},
            target_mode="external_hdd",
        )
        self.assertFalse(out["blocks_local_hdd_backup"])

    def test_cloud_blocked(self):
        out = classify_wifi_runtime_blockers(
            wifi_status={"blocks_local_hdd_backup": False, "blocks_cloud_backup": True},
            target_mode="cloud_pro",
        )
        codes = [e.get("code") for e in out["errors"]]
        self.assertIn("blocked_cloud_selected_but_wifi_missing", codes)


if __name__ == "__main__":
    unittest.main()
