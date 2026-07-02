"""Safe action policy V1 tests."""

from __future__ import annotations

import unittest

from core.rescue_repair_advice_engine_v1 import build_safe_action_plan
from core.rescue_safe_action_model_v1 import (
    SafeActionClass,
    action_allowed_without_operator,
    classify_action,
)


class RescueSafeActionPolicyV1Tests(unittest.TestCase):
    def test_destructive_blocked(self) -> None:
        defn = classify_action("efi_repair")
        assert defn is not None
        self.assertEqual(defn.action_class, SafeActionClass.DESTRUCTIVE_BLOCKED)

    def test_local_fix_allowed_without_operator(self) -> None:
        self.assertTrue(action_allowed_without_operator("wlan_rescan"))

    def test_plan_blocks_efi(self) -> None:
        plan = build_safe_action_plan(["pcie_aer_fatal"])
        blocked = [a for a in plan["actions"] if a["status"] == "blocked"]
        self.assertTrue(blocked)


if __name__ == "__main__":
    unittest.main()
