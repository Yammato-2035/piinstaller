"""Tests for canonical rescue telemetry endpoint configuration."""

from __future__ import annotations

import unittest

from core.rescue_telemetry_endpoints import LEGACY_INGEST_PATH, resolve_telemetry_urls


class RescueTelemetryEndpointsTests(unittest.TestCase):
    def test_cloud_defaults(self) -> None:
        urls = resolve_telemetry_urls()
        self.assertEqual(urls["path_style"], "cloud")
        self.assertTrue(urls["health_url"].endswith("/v1/telemetry/health"))
        self.assertTrue(urls["ingest_url"].endswith("/v1/telemetry/ingest"))

    def test_legacy_path_style(self) -> None:
        urls = resolve_telemetry_urls(
            base_url="http://192.168.178.140:8001",
            path_style="legacy",
        )
        self.assertTrue(urls["health_url"].endswith("/api/rescue/telemetry/health"))
        self.assertTrue(urls["ingest_url"].endswith(LEGACY_INGEST_PATH))


if __name__ == "__main__":
    unittest.main()
