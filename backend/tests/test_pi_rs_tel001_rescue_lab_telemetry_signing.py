"""PI-RS-TEL-001 signing tests."""

from __future__ import annotations

import unittest
import uuid

from core.rescue_lab_telemetry_model import build_synthetic_rescue_lab_payload
from core.rescue_lab_telemetry_signing import (
    build_hmac_headers,
    build_nonce,
    canonical_json_bytes,
    sign_hmac_v2,
)


class RescueLabTelemetrySigningTests(unittest.TestCase):
    def test_nonce_generated(self) -> None:
        n1 = build_nonce()
        n2 = build_nonce()
        self.assertNotEqual(n1, n2)
        uuid.UUID(n1)

    def test_canonical_hmac_stable(self) -> None:
        payload = build_synthetic_rescue_lab_payload().to_dict()
        nonce = "fixed-nonce"
        ts = "1700000000"
        secret = "test-secret-for-unit-tests-only"
        sig1 = sign_hmac_v2(payload, secret, nonce, ts, canonical=True)
        sig2 = sign_hmac_v2(payload, secret, nonce, ts, canonical=True)
        self.assertEqual(sig1, sig2)
        self.assertEqual(len(sig1), 64)

    def test_canonical_json_bytes_sorted(self) -> None:
        raw = canonical_json_bytes({"b": 1, "a": 2})
        self.assertEqual(raw, b'{"a":2,"b":1}')

    def test_build_hmac_headers_shape(self) -> None:
        payload = build_synthetic_rescue_lab_payload().to_dict()
        headers = build_hmac_headers("fake-rescue-stick-lab-client", payload, "test-secret")
        self.assertEqual(headers["X-Setuphelfer-Client-Id"], "fake-rescue-stick-lab-client")
        self.assertIn("X-Setuphelfer-Timestamp", headers)
        self.assertIn("X-Setuphelfer-Signature", headers)
        self.assertIn("X-Setuphelfer-Nonce", headers)


if __name__ == "__main__":
    unittest.main()
