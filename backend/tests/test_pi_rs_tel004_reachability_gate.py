"""PI-RS-TEL-004 cloud reachability gate tests."""

from __future__ import annotations

import unittest

from core.rescue_telemetry_cloud_reachability import (
    ENV_EXTERNAL_CALLS,
    build_cloud_reachability_summary,
    external_calls_enabled,
    probe_cloud_telemetry_health,
)


class Tel004ReachabilityGateTests(unittest.TestCase):
    def test_external_calls_default_false(self) -> None:
        self.assertFalse(external_calls_enabled({}))

    def test_skipped_when_external_calls_disabled(self) -> None:
        result = probe_cloud_telemetry_health(external_calls=False)
        self.assertFalse(result["reachable"])
        self.assertEqual(result["classification"], "external_calls_disabled")

    def test_tls_error_classified(self) -> None:
        def probe(_url: str, _timeout: float) -> tuple[int | None, str]:
            return None, "tls_error"

        result = probe_cloud_telemetry_health(external_calls=True, http_probe=probe)
        self.assertEqual(result["classification"], "tls_error")
        self.assertTrue(result.get("tls_error_documented"))

    def test_dns_error_classified(self) -> None:
        def probe(_url: str, _timeout: float) -> tuple[int | None, str]:
            return None, "dns_error"

        result = probe_cloud_telemetry_health(external_calls=True, http_probe=probe)
        self.assertEqual(result["classification"], "dns_error")

    def test_http_200_reachable(self) -> None:
        def probe(_url: str, _timeout: float) -> tuple[int | None, str]:
            return 200, "ok"

        result = probe_cloud_telemetry_health(external_calls=True, http_probe=probe)
        self.assertTrue(result["reachable"])

    def test_summary_issue_codes(self) -> None:
        summary = build_cloud_reachability_summary(
            external_calls=True,
            http_probe=lambda _u, _t: (None, "tls_error"),
        )
        self.assertIn("TELEMETRY_CLOUD_TLS_ERROR", summary["issue_codes"])


if __name__ == "__main__":
    unittest.main()
