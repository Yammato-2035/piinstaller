"""PI-RS-HW-COMPAT-PROVISION-001 Phase 10: hardware_compat_catalog.py loader tests."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.hardware_compat_catalog import (
    build_hardware_compat_catalog_diagnostics,
    load_compat_catalog,
    load_quirks,
    match_catalog_entry,
    match_quirks,
    validate_catalog_against_schema,
)

_REPO_ROOT = _backend.parent
_DATA_DIR = _REPO_ROOT / "data" / "hardware"


class TestCatalogLoading(unittest.TestCase):
    def test_catalog_loads_real_data_files(self) -> None:
        entries = load_compat_catalog(data_dir=_DATA_DIR)
        self.assertGreaterEqual(len(entries), 2)
        ids = {e["entry_id"] for e in entries}
        self.assertIn("msi-ge63-raider-rgb-8rf-ms16p5", ids)
        self.assertIn("asus-rog-strix-g513qm", ids)

    def test_catalog_is_not_exhaustive_by_design(self) -> None:
        diag = build_hardware_compat_catalog_diagnostics(data_dir=_DATA_DIR)
        self.assertFalse(diag["exhaustive"])
        self.assertLess(diag["entry_count"], 100)  # curated, not a full PCI/USB-ID dump

    def test_catalog_validates_against_own_schema(self) -> None:
        errors = validate_catalog_against_schema(data_dir=_DATA_DIR)
        self.assertEqual(errors, [], f"schema violations: {errors}")

    def test_every_entry_has_evidence_paths_that_exist_in_repo(self) -> None:
        entries = load_compat_catalog(data_dir=_DATA_DIR)
        for entry in entries:
            self.assertTrue(entry["evidence_paths"], f"{entry['entry_id']} has no evidence_paths")
            for rel_path in entry["evidence_paths"]:
                self.assertTrue(
                    (_REPO_ROOT / rel_path).exists(), f"{entry['entry_id']}: evidence path missing: {rel_path}"
                )

    def test_no_unverified_support_level_without_evidence(self) -> None:
        entries = load_compat_catalog(data_dir=_DATA_DIR)
        for entry in entries:
            if entry["support_level"] == "verified":
                self.assertIsNotNone(entry.get("last_verified_at"))


class TestCatalogMatching(unittest.TestCase):
    def test_exact_dmi_product_match(self) -> None:
        entry = match_catalog_entry(dmi_product="GE63 Raider RGB 8RF", catalog=load_compat_catalog(data_dir=_DATA_DIR))
        self.assertIsNotNone(entry)
        self.assertEqual(entry["entry_id"], "msi-ge63-raider-rgb-8rf-ms16p5")

    def test_no_match_for_unknown_product_stays_none(self) -> None:
        entry = match_catalog_entry(dmi_product="Totally Unknown Board X9000", catalog=load_compat_catalog(data_dir=_DATA_DIR))
        self.assertIsNone(entry)

    def test_vendor_product_id_exact_match_only(self) -> None:
        catalog = [
            {
                "entry_id": "test-entry",
                "match": {"vendor_id": "10de", "product_id": "249d"},
                "classification": {},
                "support_level": "verified",
                "evidence_paths": ["docs/x.md"],
            }
        ]
        self.assertIsNotNone(match_catalog_entry(vendor_id="10DE", product_id="249D", catalog=catalog))
        self.assertIsNone(match_catalog_entry(vendor_id="10de", product_id="ffff", catalog=catalog))


class TestQuirksMatching(unittest.TestCase):
    def test_quirks_load_real_data(self) -> None:
        quirks = load_quirks(data_dir=_DATA_DIR)
        self.assertGreaterEqual(len(quirks), 1)

    def test_matched_quirk_by_product_and_driver(self) -> None:
        quirks = load_quirks(data_dir=_DATA_DIR)
        matched = match_quirks(dmi_product="GE63 Raider RGB 8RF", driver_name="nouveau", quirks=quirks)
        self.assertEqual(len(matched), 1)

    def test_unmatched_quirk_stays_empty(self) -> None:
        quirks = load_quirks(data_dir=_DATA_DIR)
        matched = match_quirks(dmi_product="Some Other Board", driver_name="i915", quirks=quirks)
        self.assertEqual(matched, [])


if __name__ == "__main__":
    unittest.main()
