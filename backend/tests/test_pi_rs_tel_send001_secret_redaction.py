"""PI-RS-TEL-SEND-001 secret redaction tests."""

from __future__ import annotations

import unittest

from core.rescue_stick_cloud_lab_send import redact_secret_material


class TelSend001SecretRedactionTests(unittest.TestCase):
    def test_authorization_header_redacted(self) -> None:
        text = "Authorization: Bearer abcdef1234567890"
        redacted = redact_secret_material(text)
        self.assertNotIn("abcdef1234567890", redacted)
        self.assertIn("[redacted]", redacted)

    def test_token_in_log_line_redacted(self) -> None:
        text = "loaded token=super-secret-value from file"
        redacted = redact_secret_material(text)
        self.assertNotIn("super-secret-value", redacted)
        self.assertIn("[redacted]", redacted)


if __name__ == "__main__":
    unittest.main()
