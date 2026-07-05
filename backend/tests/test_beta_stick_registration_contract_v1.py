"""Beta stick registration contract tests."""

from __future__ import annotations

import unittest

from core.beta_stick_registration_contract_v1 import (
    detect_suspected_clone,
    upload_blocked_for_stick,
    validate_stick_registry_entry,
)


class BetaStickRegistrationContractV1Tests(unittest.TestCase):
    def test_clone_detection(self) -> None:
        self.assertTrue(
            detect_suspected_clone(
                registered_device_key_id="key-a",
                presented_device_key_id="key-b",
                stick_id_match=True,
            )
        )

    def test_team_provisioned_valid(self) -> None:
        errors = validate_stick_registry_entry(
            {
                "stick_id": "stick-001",
                "stick_type": "team_provisioned",
                "device_public_key_id": "pub-001",
                "status": "active",
            }
        )
        self.assertEqual(errors, [])

    def test_suspected_clone_blocks_upload(self) -> None:
        blocked, reason = upload_blocked_for_stick("suspected_clone")
        self.assertTrue(blocked)


if __name__ == "__main__":
    unittest.main()
