"""PI-RS-TEL-004 cloud path style / shell parity tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from core.rescue_telemetry_endpoints import resolve_telemetry_urls


class Tel004CloudPathStyleTests(unittest.TestCase):
    def test_cloud_default_paths(self) -> None:
        urls = resolve_telemetry_urls()
        self.assertTrue(urls["ingest_url"].endswith("/v1/telemetry/ingest"))
        self.assertTrue(urls["health_url"].endswith("/v1/telemetry/health"))

    def test_legacy_override_paths(self) -> None:
        urls = resolve_telemetry_urls(
            base_url="http://192.168.178.140:8001",
            path_style="legacy",
        )
        self.assertTrue(urls["health_url"].endswith("/api/rescue/telemetry/health"))
        self.assertTrue(urls["ingest_url"].endswith("/api/rescue/telemetry/v1/ingest"))

    def test_shell_common_defaults_cloud(self) -> None:
        root = Path(__file__).resolve().parents[2]
        common = (root / "scripts/rescue-live/image/setuphelfer-rescue-common.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn("SETUPHELFER_RESCUE_TELEMETRY_BASE_URL", common)
        self.assertIn("https://telemetrie.setuphelfer.de", common)
        self.assertIn('SETUPHELFER_RESCUE_TELEMETRY_PATH_STYLE="${SETUPHELFER_RESCUE_TELEMETRY_PATH_STYLE:-cloud}"', common)
        self.assertNotIn('SETUPHELFER_RESCUE_TELEMETRY_SERVER:-http://192.168.178.140:8001', common)


if __name__ == "__main__":
    unittest.main()
