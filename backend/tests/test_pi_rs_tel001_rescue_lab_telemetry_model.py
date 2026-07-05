"""PI-RS-TEL-001 model tests."""

from __future__ import annotations

import unittest

from core.rescue_lab_telemetry_model import (
    RESCUE_LAB_ENVIRONMENT,
    RESCUE_LAB_PAYLOAD_KIND,
    RESCUE_LAB_PRODUCT,
    RESCUE_LAB_SOURCE,
    build_synthetic_rescue_lab_payload,
    validate_rescue_lab_payload_no_pii,
)


class RescueLabTelemetryModelTests(unittest.TestCase):
    def test_synthetic_payload_contract_fields(self) -> None:
        payload = build_synthetic_rescue_lab_payload().to_dict()
        self.assertEqual(payload["product"], RESCUE_LAB_PRODUCT)
        self.assertEqual(payload["source"], RESCUE_LAB_SOURCE)
        self.assertEqual(payload["environment"], RESCUE_LAB_ENVIRONMENT)
        self.assertEqual(payload["payload_kind"], RESCUE_LAB_PAYLOAD_KIND)
        self.assertFalse(payload["safety"]["production_ready"])

    def test_no_pii_blocks_mac(self) -> None:
        payload = build_synthetic_rescue_lab_payload().to_dict()
        payload["mac_address"] = "aa:bb:cc:dd:ee:ff"
        ok, violations = validate_rescue_lab_payload_no_pii(payload)
        self.assertFalse(ok)
        self.assertTrue(any("mac" in v for v in violations))

    def test_no_pii_blocks_ip(self) -> None:
        payload = build_synthetic_rescue_lab_payload().to_dict()
        payload["ip_address"] = "192.168.1.10"
        ok, violations = validate_rescue_lab_payload_no_pii(payload)
        self.assertFalse(ok)
        self.assertTrue(any("ip" in v for v in violations))

    def test_no_pii_blocks_hostname(self) -> None:
        payload = build_synthetic_rescue_lab_payload().to_dict()
        payload["hostname"] = "workstation.example.com"
        ok, violations = validate_rescue_lab_payload_no_pii(payload)
        self.assertFalse(ok)
        self.assertTrue(any("hostname" in v for v in violations))

    def test_no_pii_blocks_email(self) -> None:
        payload = build_synthetic_rescue_lab_payload().to_dict()
        payload["email"] = "user@example.com"
        ok, violations = validate_rescue_lab_payload_no_pii(payload)
        self.assertFalse(ok)
        self.assertTrue(any("email" in v for v in violations))

    def test_no_pii_blocks_raw_log(self) -> None:
        payload = build_synthetic_rescue_lab_payload().to_dict()
        payload["raw_log"] = "x" * 64
        ok, violations = validate_rescue_lab_payload_no_pii(payload)
        self.assertFalse(ok)
        self.assertTrue(any("raw_log" in v for v in violations))

    def test_no_cloudserver_cross_payload(self) -> None:
        payload = build_synthetic_rescue_lab_payload().to_dict()
        payload["product"] = "setuphelfer-cloudserver-edition"
        ok, violations = validate_rescue_lab_payload_no_pii(payload)
        self.assertFalse(ok)
        self.assertTrue(any("cloudserver" in v for v in violations))


if __name__ == "__main__":
    unittest.main()
