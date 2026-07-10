"""PI-RS-TEL-004 endpoint configuration tests."""

from __future__ import annotations

import unittest

from core.rescue_telemetry_endpoints import (
    CLOUD_BASE_URL_DEFAULT,
    CLOUD_HEALTH_PATH,
    CLOUD_INGEST_PATH,
    DEFAULT_PROFILE,
    build_telemetry_health_url,
    build_telemetry_ingest_url,
    classify_endpoint_kind,
    load_rescue_telemetry_endpoint_config,
    reject_credentials_in_url,
    resolve_rescue_telemetry_profile,
    resolve_telemetry_urls,
)


class Tel004EndpointConfigTests(unittest.TestCase):
    def test_default_profile_is_cloud(self) -> None:
        cfg = load_rescue_telemetry_endpoint_config()
        self.assertEqual(cfg.get("default_profile"), DEFAULT_PROFILE)

    def test_cloud_base_url(self) -> None:
        prof = resolve_rescue_telemetry_profile()
        self.assertEqual(prof["profile"], "cloud")
        self.assertEqual(prof["base_url"], CLOUD_BASE_URL_DEFAULT)

    def test_cloud_paths(self) -> None:
        prof = resolve_rescue_telemetry_profile()
        self.assertEqual(prof["health_path"], CLOUD_HEALTH_PATH)
        self.assertEqual(prof["ingest_path"], CLOUD_INGEST_PATH)

    def test_build_urls(self) -> None:
        prof = resolve_rescue_telemetry_profile()
        self.assertEqual(
            build_telemetry_health_url(prof),
            f"{CLOUD_BASE_URL_DEFAULT}{CLOUD_HEALTH_PATH}",
        )
        self.assertEqual(
            build_telemetry_ingest_url(prof),
            f"{CLOUD_BASE_URL_DEFAULT}{CLOUD_INGEST_PATH}",
        )

    def test_legacy_only_when_explicit(self) -> None:
        prof = resolve_rescue_telemetry_profile("legacy_lan_lab")
        self.assertTrue(prof.get("legacy"))
        self.assertIn("/api/rescue/telemetry/", prof["health_path"])

    def test_credentials_rejected(self) -> None:
        with self.assertRaises(ValueError):
            reject_credentials_in_url("https://user:pass@telemetrie.setuphelfer.de")

    def test_classify_cloud_and_legacy(self) -> None:
        self.assertEqual(
            classify_endpoint_kind("https://telemetrie.setuphelfer.de/v1/telemetry/health"),
            "cloud",
        )
        self.assertEqual(
            classify_endpoint_kind("http://192.168.178.140:8001/api/rescue/telemetry/health"),
            "legacy",
        )

    def test_resolve_telemetry_urls_default_not_legacy(self) -> None:
        urls = resolve_telemetry_urls()
        self.assertEqual(urls["path_style"], "cloud")
        self.assertTrue(urls["health_url"].endswith("/v1/telemetry/health"))
        self.assertFalse(urls["health_url"].endswith("/api/rescue/telemetry/health"))


if __name__ == "__main__":
    unittest.main()
