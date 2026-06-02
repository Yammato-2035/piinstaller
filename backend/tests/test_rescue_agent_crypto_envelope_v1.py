from __future__ import annotations

import unittest

from rescue_agent.crypto_envelope import build_encrypted_envelope


class RescueAgentCryptoEnvelopeTests(unittest.TestCase):
    def test_plaintext_not_stored_in_envelope(self) -> None:
        report = {"hostname": "secret-host", "data": "abc"}
        envelope = build_encrypted_envelope(
            plaintext_report=report,
            session_id="s1",
            agent_id="a1",
            sender_public_key="spk",
            recipient_key_id="r1",
            created_at="2026-01-01T00:00:00+00:00",
        )
        self.assertNotIn("hostname", envelope)
        self.assertNotIn("secret-host", envelope["ciphertext"])

    def test_wrong_recipient_key_id_is_blocked(self) -> None:
        with self.assertRaises(ValueError):
            build_encrypted_envelope(
                plaintext_report={"x": 1},
                session_id="s1",
                agent_id="a1",
                sender_public_key="spk",
                recipient_key_id="",
                created_at="2026-01-01T00:00:00+00:00",
            )

    def test_unencrypted_fallback_is_blocked(self) -> None:
        with self.assertRaises(ValueError):
            build_encrypted_envelope(
                plaintext_report={"x": 1},
                session_id="s1",
                agent_id="a1",
                sender_public_key="spk",
                recipient_key_id="r1",
                created_at="2026-01-01T00:00:00+00:00",
                allow_unencrypted_fallback=True,
            )

    def test_replay_protection_is_todo_documented(self) -> None:
        envelope = build_encrypted_envelope(
            plaintext_report={"x": 1},
            session_id="s1",
            agent_id="a1",
            sender_public_key="spk",
            recipient_key_id="r1",
            created_at="2026-01-01T00:00:00+00:00",
        )
        self.assertIn("nonce", envelope)


if __name__ == "__main__":
    unittest.main()
