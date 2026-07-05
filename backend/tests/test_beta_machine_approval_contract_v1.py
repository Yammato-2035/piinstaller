"""Beta machine approval contract tests."""

from __future__ import annotations

import unittest

from core.beta_machine_approval_contract_v1 import (
    telemetry_mode_for_machine,
    transition_approval,
)


class BetaMachineApprovalContractV1Tests(unittest.TestCase):
    def test_pending_to_approved(self) -> None:
        self.assertEqual(transition_approval("pending", "approve"), "approved")

    def test_pending_device_approval_mode(self) -> None:
        mode = telemetry_mode_for_machine("pending", agreement_valid=True)
        self.assertEqual(mode, "restricted_local_only")


if __name__ == "__main__":
    unittest.main()
