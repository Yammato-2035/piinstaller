"""PI-RS-TEL-001 HTTP client tests (mock transport only)."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from core.rescue_lab_telemetry_config import (
    ENV_CLIENT_SECRET,
    ENV_LAB_BASE_URL,
    load_rescue_lab_telemetry_config,
)
from core.rescue_lab_telemetry_model import RescueLabTelemetryConfig
from core.rescue_lab_telemetry_client import send_rescue_lab_telemetry
from core.rescue_lab_telemetry_model import build_synthetic_rescue_lab_payload
from core.rescue_lab_telemetry_status import reset_last_send_status_for_tests


class RescueLabTelemetryClientTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_last_send_status_for_tests()

    def tearDown(self) -> None:
        reset_last_send_status_for_tests()

    def test_missing_secret_blocked(self) -> None:
        config = RescueLabTelemetryConfig(
            lab_base_url="http://127.0.0.1:9999",
            client_id="fake-rescue-stick-lab-client",
            secret=None,
        )
        result = send_rescue_lab_telemetry(config, build_synthetic_rescue_lab_payload().to_dict())
        self.assertEqual(result.status, "blocked_missing_secret")

    def test_maps_202_accepted(self) -> None:
        config = RescueLabTelemetryConfig(
            lab_base_url="http://127.0.0.1:9999",
            client_id="fake-rescue-stick-lab-client",
            secret="test-secret",
        )

        def mock_post(envelope):  # noqa: ANN001
            return 202, {"reason_code": "accepted_rescue_lab_telemetry"}

        result = send_rescue_lab_telemetry(
            config,
            build_synthetic_rescue_lab_payload().to_dict(),
            http_post=mock_post,
        )
        self.assertEqual(result.status, "accepted_rescue_lab_telemetry")
        self.assertEqual(result.http_status, 202)

    def test_maps_401_rejected_auth(self) -> None:
        config = RescueLabTelemetryConfig(
            lab_base_url="http://127.0.0.1:9999",
            client_id="fake-rescue-stick-lab-client",
            secret="test-secret",
        )

        def mock_post(envelope):  # noqa: ANN001
            return 401, {"reason_code": "invalid_signature"}

        result = send_rescue_lab_telemetry(
            config,
            build_synthetic_rescue_lab_payload().to_dict(),
            http_post=mock_post,
        )
        self.assertEqual(result.status, "rejected_auth")

    def test_maps_403_product_rejection(self) -> None:
        config = RescueLabTelemetryConfig(
            lab_base_url="http://127.0.0.1:9999",
            client_id="fake-rescue-stick-lab-client",
            secret="test-secret",
        )

        def mock_post(envelope):  # noqa: ANN001
            return 403, {"reason_code": "product_not_allowed"}

        result = send_rescue_lab_telemetry(
            config,
            build_synthetic_rescue_lab_payload().to_dict(),
            http_post=mock_post,
        )
        self.assertEqual(result.status, "rejected_product_source_or_environment")

    def test_maps_409_replay_nonce(self) -> None:
        config = RescueLabTelemetryConfig(
            lab_base_url="http://127.0.0.1:9999",
            client_id="fake-rescue-stick-lab-client",
            secret="test-secret",
        )

        def mock_post(envelope):  # noqa: ANN001
            return 409, {"reason_code": "replay_nonce"}

        result = send_rescue_lab_telemetry(
            config,
            build_synthetic_rescue_lab_payload().to_dict(),
            http_post=mock_post,
        )
        self.assertEqual(result.status, "replay_nonce")
        self.assertEqual(result.nonce_status, "replay")

    def test_load_config_from_env(self) -> None:
        with patch.dict(
            os.environ,
            {
                ENV_LAB_BASE_URL: "http://lab.example.test",
                ENV_CLIENT_SECRET: "unit-test-secret",
            },
            clear=False,
        ):
            cfg = load_rescue_lab_telemetry_config()
            self.assertEqual(cfg.lab_base_url, "http://lab.example.test")
            self.assertEqual(cfg.secret, "unit-test-secret")


if __name__ == "__main__":
    unittest.main()
