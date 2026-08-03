"""PI-RS-HW-COMPAT-PROVISION-001 Phase 13: provisioning.os_catalog tests.

Fixture groups per spec PHASE 17: invalid OS catalog entry, wrong checksum, missing
signature, incompatible architecture.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from provisioning.os_catalog import (
    build_os_catalog_diagnostics,
    filter_by_architecture,
    get_os_catalog_entry,
    load_os_catalog,
    validate_os_catalog_download_disabled,
)

_REPO_ROOT = _backend.parent
_DATA_DIR = _REPO_ROOT / "data" / "provisioning"


class TestOsCatalogLoading(unittest.TestCase):
    def test_catalog_loads_real_entries(self) -> None:
        entries = load_os_catalog(data_dir=_DATA_DIR)
        self.assertGreaterEqual(len(entries), 10)
        ids = {e["image_id"] for e in entries}
        self.assertIn("debian-13-stable-amd64-netinst", ids)
        self.assertIn("raspberry-pi-os-bookworm-arm64", ids)
        self.assertIn("proxmox-ve-future", ids)

    def test_every_entry_has_download_disabled(self) -> None:
        violations = validate_os_catalog_download_disabled(data_dir=_DATA_DIR)
        self.assertEqual(violations, [], f"entries with download enabled: {violations}")

    def test_no_fabricated_checksums(self) -> None:
        """sha256 must be null unless a real, verified value exists — spec forbids
        fabricated proof-of-integrity data."""
        for entry in load_os_catalog(data_dir=_DATA_DIR):
            if entry.get("support_status") != "verified":
                self.assertIsNone(entry.get("sha256"))

    def test_future_categories_marked_future_not_experimental(self) -> None:
        proxmox = get_os_catalog_entry("proxmox-ve-future", data_dir=_DATA_DIR)
        self.assertEqual(proxmox["support_status"], "future")

    def test_filter_by_architecture(self) -> None:
        arm_entries = filter_by_architecture(load_os_catalog(data_dir=_DATA_DIR), "aarch64")
        self.assertGreater(len(arm_entries), 0)
        for e in arm_entries:
            self.assertEqual(e["architecture"], "aarch64")

    def test_diagnostics_shape(self) -> None:
        diag = build_os_catalog_diagnostics(data_dir=_DATA_DIR)
        self.assertFalse(diag["download_ever_enabled"])
        self.assertGreater(diag["support_status_counts"]["future"], 0)


if __name__ == "__main__":
    unittest.main()
