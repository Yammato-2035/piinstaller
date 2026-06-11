"""Phase A.1: safety_facade public contracts — contexts, types, no shell."""

from __future__ import annotations

import inspect
import unittest

from core.safety_facade import (
    FACADE_CONTRACT_VERSION,
    SafetyContext,
    SafetyDecision,
    build_safety_decision,
    build_safety_decision_contract,
    validate_backup_target,
    validate_partition_target,
    validate_restore_target,
)


class SafetyFacadeContractsV1Tests(unittest.TestCase):
    def test_safety_context_enum(self) -> None:
        self.assertEqual(SafetyContext.LIVE.value, "live")
        self.assertEqual(SafetyContext.RESCUE.value, "rescue")
        self.assertEqual(SafetyContext.PARTITION_HELPER.value, "partition_helper")
        self.assertEqual(SafetyContext.CLOUDSERVER_FUTURE.value, "cloudserver_future")

    def test_validate_backup_target_alias(self) -> None:
        out = validate_backup_target("/dev/sdb1", context=SafetyContext.LIVE)
        self.assertIn("allowed", out)
        self.assertEqual(out["context"], "live")
        self.assertEqual(out.get("facade_version", FACADE_CONTRACT_VERSION), FACADE_CONTRACT_VERSION)

    def test_validate_restore_target_contract(self) -> None:
        out = validate_restore_target("/dev/sdb1", context="rescue")
        self.assertIn("restore_allowed", out)

    def test_validate_partition_target_contract(self) -> None:
        out = validate_partition_target("/dev/sdb1", context=SafetyContext.PARTITION_HELPER)
        self.assertIn("partition_allowed", out)
        self.assertEqual(out["context"], "partition_helper")

    def test_build_safety_decision_contract_wrapper(self) -> None:
        raw = build_safety_decision(target="/dev/sdb", context=SafetyContext.RESCUE)
        self.assertEqual(raw["facade_version"], FACADE_CONTRACT_VERSION)
        typed = build_safety_decision_contract(target="/dev/sdb", context=SafetyContext.RESCUE)
        self.assertIsInstance(typed, SafetyDecision)
        self.assertEqual(typed.context, SafetyContext.RESCUE)

    def test_no_subprocess_in_facade_module_contract_layer(self) -> None:
        import core.safety_facade as mod

        src = inspect.getsource(mod)
        self.assertNotIn("subprocess", src)


if __name__ == "__main__":
    unittest.main()
