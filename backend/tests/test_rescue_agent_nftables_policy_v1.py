from __future__ import annotations

import unittest

from rescue_agent.nftables_policy import build_nftables_policy_preview


class RescueAgentNftablesPolicyTests(unittest.TestCase):
    def test_default_inbound_drop_set(self) -> None:
        policy = build_nftables_policy_preview(discovery_phase=False, validated_endpoint=False)
        self.assertEqual(policy["inbound_default"], "drop")

    def test_ssh_inbound_not_allowed(self) -> None:
        policy = build_nftables_policy_preview(discovery_phase=False, validated_endpoint=True)
        self.assertNotIn("ssh", policy["allowed_services"])

    def test_mdns_only_in_discovery_phase(self) -> None:
        yes = build_nftables_policy_preview(discovery_phase=True, validated_endpoint=False)
        no = build_nftables_policy_preview(discovery_phase=False, validated_endpoint=False)
        self.assertIn("mdns_discovery_temporary", yes["allowed_services"])
        self.assertNotIn("mdns_discovery_temporary", no["allowed_services"])

    def test_devserver_outbound_only_after_endpoint_validation(self) -> None:
        yes = build_nftables_policy_preview(discovery_phase=False, validated_endpoint=True)
        no = build_nftables_policy_preview(discovery_phase=False, validated_endpoint=False)
        self.assertIn("devserver_session", yes["allowed_services"])
        self.assertNotIn("devserver_session", no["allowed_services"])

    def test_apply_disallowed_and_mandatory_true(self) -> None:
        policy = build_nftables_policy_preview(discovery_phase=False, validated_endpoint=True)
        self.assertFalse(policy["apply_allowed"])
        self.assertTrue(policy["mandatory"])


if __name__ == "__main__":
    unittest.main()
