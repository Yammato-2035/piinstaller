from __future__ import annotations

import unittest

from rescue_agent.system_report import build_rescue_system_report


class RescueAgentSystemReportTests(unittest.TestCase):
    def _build(self) -> dict:
        return build_rescue_system_report(
            agent_id="agent-1",
            session_id="session-1",
            discovery_result={"discovery_status": "found", "endpoint_hash": "abc"},
            e2ee_status="required",
        )

    def test_report_contains_required_fields(self) -> None:
        report = self._build()
        self.assertEqual(report["schema_version"], "1.0")
        self.assertEqual(report["agent_id"], "agent-1")
        self.assertIn("storage", report)

    def test_write_operations_stay_false(self) -> None:
        report = self._build()
        self.assertFalse(report["safety"]["write_operations_allowed"])

    def test_no_plain_serial_in_identity(self) -> None:
        report = self._build()
        self.assertIsNone(report["identity"]["device_identity"]["serial_hash"])

    def test_report_hash_is_reproducible(self) -> None:
        one = self._build()
        two = self._build()
        self.assertEqual(len(one["evidence"]["report_hash"]), 64)
        self.assertEqual(len(two["evidence"]["report_hash"]), 64)


if __name__ == "__main__":
    unittest.main()
