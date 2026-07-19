"""Lab auto discovery re-arms when one-shot run-control is stale."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.rescue_auto_discovery_start_gate import (  # noqa: E402
    EXIT_START,
    evaluate_discovery_start_gate,
)
from core.rescue_discovery_run_control import (  # noqa: E402
    build_discovery_run_control,
    write_discovery_run_control,
)


class LabAutoDiscoveryRearmTests(unittest.TestCase):
    def test_stale_consumed_control_rearmed_under_lab_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            ctrl = build_discovery_run_control(
                expected_payload_version="1.10.0.36",
                expected_machine_family="",
            )
            ctrl["enabled"] = False
            ctrl["consumed"] = True
            write_discovery_run_control(base, ctrl)
            with patch(
                "core.rescue_auto_discovery_start_gate._machine_family_plausible",
                return_value=True,
            ):
                result = evaluate_discovery_start_gate(
                    setup_logs_base=base,
                    cmdline={"setuphelfer_auto_discovery=1", "setuphelfer_msi_lab_auto=1"},
                    payload_version="1.10.0.36",
                )
        self.assertTrue(result["start_allowed"])
        self.assertEqual(result["exit_code"], EXIT_START)
        self.assertEqual(result["reason"], "lab_auto_discovery_stale_control_rearmed")

    def test_payload_mismatch_bypassed_under_lab_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            ctrl = build_discovery_run_control(
                expected_payload_version="1.10.0.30",
                expected_machine_family="",
            )
            write_discovery_run_control(base, ctrl)
            with patch(
                "core.rescue_auto_discovery_start_gate._machine_family_plausible",
                return_value=True,
            ):
                with patch(
                    "core.rescue_auto_discovery_start_gate.resolve_run_mode",
                    return_value={"ok": True, "run_mode": "auto_discovery_only"},
                ):
                    result = evaluate_discovery_start_gate(
                        setup_logs_base=base,
                        cmdline={"setuphelfer_auto_discovery=1", "setuphelfer_msi_lab_auto=1"},
                        payload_version="1.10.0.36",
                    )
        self.assertTrue(result["start_allowed"])
        self.assertEqual(result["reason"], "lab_auto_discovery_payload_version_bypass")


if __name__ == "__main__":
    unittest.main()
