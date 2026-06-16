"""Public-safe redaction contract tests."""

from __future__ import annotations

import unittest

from core.redaction_contract import REDACTION_TEST_VECTORS, redact_text, validate_test_vectors


class RedactionContractV1Tests(unittest.TestCase):
    def test_all_vectors_pass(self) -> None:
        failures = validate_test_vectors()
        self.assertEqual(failures, [], msg=str(failures))

    def test_ip_redacted(self) -> None:
        result = redact_text("server 10.0.0.5 ok")
        self.assertIn("ipv4", result.categories_matched)
        self.assertNotIn("10.0.0.5", result.redacted_text)

    def test_token_redacted(self) -> None:
        result = redact_text("key ghp_abcdefghijklmnopqrstuvwxyz1234567890 end")
        self.assertIn("api_token", result.categories_matched)

    def test_vectors_count(self) -> None:
        self.assertGreaterEqual(len(REDACTION_TEST_VECTORS), 5)


if __name__ == "__main__":
    unittest.main()
