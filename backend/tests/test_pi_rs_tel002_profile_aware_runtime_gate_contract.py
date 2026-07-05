"""PI-RS-TEL-002 profile-aware runtime gate contract tests."""

from __future__ import annotations

import unittest

from core.profile_aware_runtime_gate import evaluate_profile_aware_runtime_gate


class ProfileAwareRuntimeGateContractTests(unittest.TestCase):
    def test_release_accepts_dcc_404(self) -> None:
        result = evaluate_profile_aware_runtime_gate(
            expected_profile="release",
            version_http_status=200,
            version_payload={"project_version": "1.9.19.3", "backend_runtime_path": "/opt/setuphelfer/backend"},
            lab_status_http=403,
            lab_status_body={"errors": ["feature_disabled:lab"]},
            dcc_status_http=404,
            service_active=True,
        )
        self.assertEqual(result["status"], "release_runtime_ok")
        self.assertNotIn("dcc_404_expected_in_release", result.get("warnings", []))

    def test_release_requires_lab_disabled(self) -> None:
        result = evaluate_profile_aware_runtime_gate(
            expected_profile="release",
            version_http_status=200,
            version_payload={"project_version": "1.0.0"},
            lab_status_http=200,
            lab_status_body={"feature_enabled": True, "client_id": "fake-rescue-stick-lab-client"},
            dcc_status_http=404,
            service_active=True,
        )
        self.assertTrue(result["status"].endswith("_blocked"))
        self.assertIn("release_requires_lab_endpoints_disabled", result["errors"])

    def test_lab_requires_lab_enabled(self) -> None:
        result = evaluate_profile_aware_runtime_gate(
            expected_profile="local_lab",
            version_http_status=200,
            version_payload={"project_version": "1.0.0"},
            lab_status_http=200,
            lab_status_body={"feature_enabled": True, "client_id": "fake-rescue-stick-lab-client"},
            dcc_status_http=200,
            service_active=True,
        )
        self.assertEqual(result["status"], "lab_runtime_ok")

    def test_lab_blocks_feature_disabled(self) -> None:
        result = evaluate_profile_aware_runtime_gate(
            expected_profile="developer",
            version_http_status=200,
            version_payload={"project_version": "1.0.0"},
            lab_status_http=403,
            lab_status_body={"errors": ["feature_disabled"]},
            dcc_status_http=200,
            service_active=True,
        )
        self.assertTrue(result["status"].endswith("_blocked"))
        self.assertIn("lab_profile_requires_lab_endpoints_enabled", result["errors"])

    def test_gate_output_shape(self) -> None:
        result = evaluate_profile_aware_runtime_gate(
            expected_profile="release",
            version_http_status=200,
            version_payload={"project_version": "1.0.0"},
            lab_status_http=403,
            lab_status_body={},
            dcc_status_http=404,
            service_active=True,
        )
        self.assertIn("profile", result)
        self.assertIn("status", result)
        self.assertIn("warnings", result)
        self.assertIn("errors", result)


if __name__ == "__main__":
    unittest.main()
