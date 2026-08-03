"""PI-RS-HW-COMPAT-PROVISION-001 Phase 11: raspberry_pi_compatibility.py + os_plan.py."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from platforms.raspberry_pi_compatibility import build_compatibility_summary, build_raspberry_pi_compatibility_diagnostics
from platforms.raspberry_pi_os_plan import build_os_candidate_matrix, build_raspberry_pi_os_plan_diagnostics


class TestCompatibilitySummary(unittest.TestCase):
    def test_pi3_and_pi5_have_different_limitations(self) -> None:
        pi3 = build_compatibility_summary(model_id="pi3")
        pi5 = build_compatibility_summary(model_id="pi5")
        self.assertNotEqual(pi3["known_limitations"], pi5["known_limitations"])
        self.assertIn("max_ram_1gb", pi3["known_limitations"])
        self.assertNotIn("max_ram_1gb", pi5["known_limitations"])

    def test_unidentified_model_is_explicit_unknown(self) -> None:
        result = build_compatibility_summary(model_id=None)
        self.assertEqual(result["compatibility_status"], "unknown")

    def test_no_blanket_pi_3_to_5_claim(self) -> None:
        diag = build_raspberry_pi_compatibility_diagnostics()
        self.assertFalse(diag["blanket_pi_3_to_5_claim_allowed"])

    def test_physical_validation_always_required(self) -> None:
        pi4 = build_compatibility_summary(model_id="pi4")
        self.assertTrue(pi4["physical_validation_required"])


class TestOsCandidateMatrix(unittest.TestCase):
    def test_pi3_1gb_blocks_ubuntu_desktop(self) -> None:
        rows = build_os_candidate_matrix(model_id="pi3", ram_variants_gb=[1])
        ubuntu_desktop = next(r for r in rows if r["os_id"] == "ubuntu_desktop_arm64")
        self.assertFalse(ubuntu_desktop["ram_sufficient_for_smallest_known_variant"])
        self.assertEqual(ubuntu_desktop["support_status"], "blocked")

    def test_pi5_8gb_variant_allows_all_candidates_ram_wise(self) -> None:
        """Only the 8 GB variant is known to exist here, so it is also the smallest."""
        rows = build_os_candidate_matrix(model_id="pi5", ram_variants_gb=[8])
        for row in rows:
            self.assertTrue(row["ram_sufficient_for_smallest_known_variant"] in (True, None))

    def test_pi5_2gb_variant_blocks_ubuntu_desktop_but_not_server(self) -> None:
        rows = build_os_candidate_matrix(model_id="pi5", ram_variants_gb=[2, 4, 8])
        ubuntu_desktop = next(r for r in rows if r["os_id"] == "ubuntu_desktop_arm64")
        ubuntu_server = next(r for r in rows if r["os_id"] == "ubuntu_server_arm64")
        self.assertFalse(ubuntu_desktop["ram_sufficient_for_smallest_known_variant"])
        self.assertTrue(ubuntu_server["ram_sufficient_for_smallest_known_variant"])

    def test_every_row_starts_as_planned_not_verified(self) -> None:
        rows = build_os_candidate_matrix(model_id="pi4", ram_variants_gb=[1, 2, 4, 8])
        for row in rows:
            self.assertEqual(row["test_status"], "planned")

    def test_no_model_returns_empty(self) -> None:
        self.assertEqual(build_os_candidate_matrix(model_id=None, ram_variants_gb=[]), [])

    def test_diagnostics_never_installs(self) -> None:
        diag = build_raspberry_pi_os_plan_diagnostics()
        self.assertFalse(diag["install_triggered"])
        self.assertIn("physically_verified", diag["valid_test_status_values"])


if __name__ == "__main__":
    unittest.main()
