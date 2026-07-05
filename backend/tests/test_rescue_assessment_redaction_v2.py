"""Assessment redaction V2 tests."""

from __future__ import annotations

import unittest

from core.rescue_assessment_redaction import redact_assessment_payload, scan_forbidden_fields


class RescueAssessmentRedactionV2Tests(unittest.TestCase):
    def test_redacts_mac_ip_email_serial(self) -> None:
        raw = {
            "network": "MAC aa:bb:cc:dd:ee:ff IP 192.168.1.10 user@test.example",
            "serial": "ABC1234567890XYZ",
        }
        redacted, report = redact_assessment_payload(raw)
        blob = str(redacted)
        self.assertNotIn("aa:bb:cc:dd:ee:ff", blob)
        self.assertNotIn("192.168.1.10", blob)
        self.assertNotIn("user@test.example", blob)
        self.assertFalse(report["contains_mac"])
        self.assertFalse(report["contains_ip"])

    def test_no_file_lists(self) -> None:
        raw = {"file_list": ["/home/user/secret.txt"]}
        forbidden = scan_forbidden_fields(raw)
        self.assertIn("contains_file_list", forbidden)


if __name__ == "__main__":
    unittest.main()
