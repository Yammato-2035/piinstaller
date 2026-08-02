"""Driver catalog lookup tests."""

from __future__ import annotations

import unittest

from core.driver_catalog import DRIVER_CATALOG, match_driver_hint


class DriverCatalogTests(unittest.TestCase):
    def test_matches_known_vendor_keyword(self) -> None:
        hint = match_driver_hint("NVIDIA Corporation GeForce RTX 3060")
        self.assertIsNotNone(hint)
        self.assertEqual(hint["vendor"], "NVIDIA")
        self.assertTrue(hint["official_url"].startswith("https://"))

    def test_matches_printer_vendor(self) -> None:
        hint = match_driver_hint("Canon PIXMA MG3650 series")
        self.assertIsNotNone(hint)
        self.assertEqual(hint["vendor"], "Canon")

    def test_no_match_returns_none(self) -> None:
        self.assertIsNone(match_driver_hint("Totally Unknown Device Co."))

    def test_no_match_on_empty_text(self) -> None:
        self.assertIsNone(match_driver_hint(""))

    def test_catalog_entries_have_https_urls(self) -> None:
        for entry in DRIVER_CATALOG:
            with self.subTest(vendor=entry["vendor"]):
                self.assertTrue(entry["official_url"].startswith("https://"))


if __name__ == "__main__":
    unittest.main()
