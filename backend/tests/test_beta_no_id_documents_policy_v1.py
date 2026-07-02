"""Beta no ID documents policy tests."""

from __future__ import annotations

import unittest

from core.beta_agreement_gate_v1 import FORBIDDEN_ID_DOCUMENT_FIELDS, validate_no_id_documents


class BetaNoIdDocumentsPolicyV1Tests(unittest.TestCase):
    def test_ausweis_blocked(self) -> None:
        violations = validate_no_id_documents({"personalausweis": "scan.pdf"})
        self.assertTrue(violations)

    def test_clean_registration_payload(self) -> None:
        violations = validate_no_id_documents(
            {"email_hash": "sha256:abc", "mfa_method": "totp"}
        )
        self.assertEqual(violations, [])

    def test_forbidden_fields_documented(self) -> None:
        self.assertIn("ausweisnummer", FORBIDDEN_ID_DOCUMENT_FIELDS)


if __name__ == "__main__":
    unittest.main()
