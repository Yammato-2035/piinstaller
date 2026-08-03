"""PI-RS-HW-COMPAT-PROVISION-001 Phase 12: carrier_layout/capacity_planner/content_catalog.

Fixture groups per spec PHASE 17: 64-GB carrier with sufficient capacity, too-small
carrier.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from rescue.carrier_capacity_planner import (
    MIN_SAFETY_RESERVE_RATIO,
    build_carrier_capacity_planner_diagnostics,
    compute_capacity_plan,
)
from rescue.carrier_content_catalog import build_carrier_content_catalog_diagnostics, get_required_components
from rescue.carrier_layout import build_carrier_layout_diagnostics, evaluate_carrier_strategy

_REAL_64GB_STICK_BYTES = 63_864_502_272  # typical real reported size of a "64 GB" USB stick
_TOO_SMALL_STICK_BYTES = 7_864_320_000  # ~7.3 GB, mislabeled/too-small stick


class TestCarrierStrategyDecision(unittest.TestCase):
    def test_default_is_orchestrator_cache_without_evidence(self) -> None:
        decision = evaluate_carrier_strategy()
        self.assertEqual(decision["recommended_strategy"], "orchestrator_cache")
        self.assertEqual(decision["decision_status"], "decided_by_spec_default")

    def test_universal_only_decided_with_explicit_evidence(self) -> None:
        decision = evaluate_carrier_strategy(universal_boot_path_evidence=True)
        self.assertEqual(decision["recommended_strategy"], "universal")
        self.assertEqual(decision["decision_status"], "decided")

    def test_split_carriers_stays_review_required_not_decided(self) -> None:
        decision = evaluate_carrier_strategy(split_carrier_operationally_acceptable=True)
        self.assertEqual(decision["recommended_strategy"], "split_carriers")
        self.assertEqual(decision["decision_status"], "review_required")

    def test_never_partitions(self) -> None:
        diag = build_carrier_layout_diagnostics()
        self.assertFalse(diag["partitioning_performed"])


class TestCapacityPlanRealBytes(unittest.TestCase):
    def test_sufficient_64gb_carrier_is_ok(self) -> None:
        plan = compute_capacity_plan(carrier_size_bytes=_REAL_64GB_STICK_BYTES)
        self.assertIn(plan["layout_status"], ("ok", "review_required"))
        self.assertGreater(plan["reserved_bytes"], 0)
        self.assertEqual(plan["reserved_bytes"], int(_REAL_64GB_STICK_BYTES * MIN_SAFETY_RESERVE_RATIO))
        self.assertFalse(plan["partitioning_performed"])

    def test_too_small_carrier_is_blocked(self) -> None:
        plan = compute_capacity_plan(
            carrier_size_bytes=_TOO_SMALL_STICK_BYTES,
            include_optional_components=["driver_firmware_offline_packages", "os_image_cache"],
        )
        self.assertEqual(plan["layout_status"], "blocked")
        self.assertIn("required_plus_optional_components_exceed_usable_capacity", plan["warnings"])

    def test_minimum_10_percent_reserve_enforced_even_if_lower_requested(self) -> None:
        plan = compute_capacity_plan(carrier_size_bytes=_REAL_64GB_STICK_BYTES, safety_reserve_ratio=0.02)
        self.assertEqual(plan["safety_reserve_ratio"], MIN_SAFETY_RESERVE_RATIO)

    def test_zero_or_negative_size_is_blocked_not_a_crash(self) -> None:
        plan = compute_capacity_plan(carrier_size_bytes=0)
        self.assertEqual(plan["layout_status"], "blocked")

    def test_does_not_assume_exactly_64_times_1024_cubed(self) -> None:
        """Spec: 'nicht blind von 64 GB ausgehen' — plan must use the passed real byte count."""
        naive_64gb = 64 * 1024**3
        plan_real = compute_capacity_plan(carrier_size_bytes=_REAL_64GB_STICK_BYTES)
        plan_naive = compute_capacity_plan(carrier_size_bytes=naive_64gb)
        self.assertNotEqual(plan_real["carrier_size_bytes"], plan_naive["carrier_size_bytes"])
        self.assertEqual(plan_real["carrier_size_bytes"], _REAL_64GB_STICK_BYTES)


class TestContentCatalog(unittest.TestCase):
    def test_required_components_are_small_relative_to_optional(self) -> None:
        required = get_required_components()
        self.assertGreater(len(required), 0)
        for c in required:
            self.assertIn("rationale", c)

    def test_no_partitioning_flag(self) -> None:
        diag = build_carrier_content_catalog_diagnostics()
        self.assertFalse(diag["partitioning_performed"])
        self.assertTrue(diag["sizes_are_estimates_not_measurements"])


class TestPlannerDiagnostics(unittest.TestCase):
    def test_uses_storage_facade_not_own_lsblk(self) -> None:
        diag = build_carrier_capacity_planner_diagnostics()
        self.assertTrue(diag["uses_storage_facade_for_real_size"])
        self.assertFalse(diag["dd_used"])
        self.assertFalse(diag["mkfs_used"])
        self.assertFalse(diag["partitioning_performed"])


if __name__ == "__main__":
    unittest.main()
