"""PI-RS-TEL-002 reachability model tests."""

from __future__ import annotations

import unittest

from core.rescue_lab_telemetry_reachability import (
    build_reachability_summary,
    check_telemetry_endpoint_reachability,
    redact_lab_url,
    reset_reachability_for_tests,
)


class ReachabilityModelTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_reachability_for_tests()

    def tearDown(self) -> None:
        reset_reachability_for_tests()

    def test_missing_base_url_blocked(self) -> None:
        summary = build_reachability_summary(profile_allowed=True, lab_base_url=None, secret="s")
        self.assertEqual(summary["network_state"], "blocked_missing_config")
        self.assertEqual(summary["telemetry_reachability"], "skipped_missing_config")

    def test_missing_secret_blocked(self) -> None:
        summary = build_reachability_summary(
            profile_allowed=True,
            lab_base_url="http://lab.example.test",
            secret=None,
        )
        self.assertEqual(summary["network_state"], "blocked_missing_secret")

    def test_release_profile_blocked(self) -> None:
        summary = build_reachability_summary(profile_allowed=False)
        self.assertEqual(summary["network_state"], "blocked_profile_disabled")

    def test_timeout_classified(self) -> None:
        def probe(_url: str, _timeout: float) -> tuple[int | None, str]:
            return None, "timeout"

        result = check_telemetry_endpoint_reachability(
            "http://lab.example.test",
            http_probe=probe,
        )
        self.assertEqual(result, "timeout")

    def test_dns_error_classified(self) -> None:
        def probe(_url: str, _timeout: float) -> tuple[int | None, str]:
            return None, "dns_error"

        result = check_telemetry_endpoint_reachability(
            "http://lab.example.test",
            http_probe=probe,
        )
        self.assertEqual(result, "dns_error")

    def test_tls_error_classified(self) -> None:
        def probe(_url: str, _timeout: float) -> tuple[int | None, str]:
            return None, "tls_error"

        result = check_telemetry_endpoint_reachability(
            "https://lab.example.test",
            http_probe=probe,
        )
        self.assertEqual(result, "tls_error")

    def test_http_200_reachable(self) -> None:
        def probe(_url: str, _timeout: float) -> tuple[int | None, str]:
            return 200, "ok"

        result = check_telemetry_endpoint_reachability(
            "http://lab.example.test",
            http_probe=probe,
        )
        self.assertEqual(result, "reachable")

    def test_summary_has_no_pii(self) -> None:
        summary = build_reachability_summary(
            profile_allowed=True,
            lab_base_url="https://lab.example.test/private",
            secret="test-secret",
            http_probe=lambda _u, _t: (200, "ok"),
        )
        blob = str(summary)
        self.assertNotIn("test-secret", blob)
        self.assertEqual(summary["lab_base_url_redacted"], "https://lab.example.test/[redacted]")
        self.assertNotIn("private", summary.get("lab_base_url_redacted", ""))


if __name__ == "__main__":
    unittest.main()
