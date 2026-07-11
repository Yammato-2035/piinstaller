"""PI-RS-TEL-SEND-001 payload redaction tests."""

from __future__ import annotations

import unittest

from core.rescue_stick_cloud_lab_payload import (
    assert_no_pii_in_payload,
    build_rescue_stick_lab_payload,
)


class TelSend001PayloadRedactionTests(unittest.TestCase):
    def test_minimal_payload_has_no_pii(self) -> None:
        payload = build_rescue_stick_lab_payload(stick_version="1.9.19.5")
        assert_no_pii_in_payload(payload)

    def test_forbidden_hostname_key_rejected(self) -> None:
        payload = build_rescue_stick_lab_payload(stick_version="1.9.19.5")
        payload["hostname"] = "secret-host.example"
        with self.assertRaises(ValueError):
            assert_no_pii_in_payload(payload)

    def test_forbidden_ipv4_rejected(self) -> None:
        payload = build_rescue_stick_lab_payload(stick_version="1.9.19.5")
        payload["note"] = "seen 192.168.1.10"
        with self.assertRaises(ValueError):
            assert_no_pii_in_payload(payload)


if __name__ == "__main__":
    unittest.main()
