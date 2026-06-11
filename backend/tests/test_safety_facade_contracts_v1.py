"""Phase A.1: safety_facade public contracts — contexts, types, no shell."""

from __future__ import annotations

import inspect
import unittest

from core.safety_facade import (
    FACADE_CONTRACT_VERSION,
    SafetyContext,
    SafetyDecision,
    WriteTargetProtectionError,
    build_safety_decision,
    build_safety_decision_contract,
    build_safety_decision_from_legacy_result,
    evaluate_preflight_write_target,
    normalize_legacy_safety_result,
    validate_backup_target,
    validate_backup_target_for_write,
    validate_partition_target,
    validate_preflight_backup_target,
    validate_restore_target,
    validate_restore_target_for_write,
    validate_write_target,
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
        self.assertNotIn("subprocess.run", src)
        self.assertNotIn("subprocess.Popen", src)

    def test_validate_preflight_backup_target_preserves_reason_codes(self) -> None:
        ir = {
            "storage": {
                "devices_classified": [
                    {
                        "device": "/dev/sdz",
                        "type": "disk",
                        "partitions": [
                            {
                                "device": "/dev/sdz1",
                                "type": "part",
                                "category": "backup_candidate",
                            }
                        ],
                    }
                ],
                "mountability": [],
            },
            "filesystems": {"detected": {"/dev/sdz1": {"type": "ext4"}}},
        }
        out = validate_preflight_backup_target("/dev/sdz", ir)
        self.assertEqual(out["reason_code"], "SAFETY_BACKUP_TARGET_OK")
        self.assertTrue(out["allowed"])
        same = evaluate_preflight_write_target("/dev/sdz", ir)
        self.assertEqual(same["reason_code"], out["reason_code"])

    def test_normalize_legacy_safety_result(self) -> None:
        raw = {
            "allowed": False,
            "reason_code": "SAFETY_SYSTEM_DISK",
            "risk_level": "high",
            "requires_confirmation": True,
            "requires_override": True,
        }
        dec = normalize_legacy_safety_result(raw, context=SafetyContext.LIVE, target="/dev/sda")
        self.assertIsInstance(dec, SafetyDecision)
        self.assertEqual(dec.reason_code, "SAFETY_SYSTEM_DISK")
        typed = build_safety_decision_from_legacy_result(
            raw, context=SafetyContext.RESCUE, target="/dev/sda"
        )
        self.assertEqual(typed.context, SafetyContext.RESCUE)

    def test_validate_backup_target_for_write_and_restore_for_write_present(self) -> None:
        self.assertTrue(callable(validate_backup_target_for_write))
        self.assertTrue(callable(validate_restore_target_for_write))
        self.assertTrue(callable(validate_write_target))
        self.assertTrue(issubclass(WriteTargetProtectionError, Exception))


if __name__ == "__main__":
    unittest.main()
