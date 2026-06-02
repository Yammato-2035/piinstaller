from __future__ import annotations

import unittest

from rescue_agent.registration import build_pairing_response


class RescueAgentRegistrationTests(unittest.TestCase):
    def test_release_blocks_without_explicit_enable(self) -> None:
        result = build_pairing_response(
            profile="release",
            rescue_pairing_enabled=False,
            session_id="s1",
            server_public_key="pk",
        )
        self.assertEqual(result["registration_status"], "rejected")

    def test_local_lab_returns_pending(self) -> None:
        result = build_pairing_response(
            profile="local_lab",
            rescue_pairing_enabled=True,
            session_id="s2",
            server_public_key="pk",
        )
        self.assertEqual(result["registration_status"], "pending")
        self.assertIn("heartbeat", result["allowed_scopes"])


if __name__ == "__main__":
    unittest.main()
