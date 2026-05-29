from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.rescue_iso_controlled_build_gate import (  # noqa: E402
    CHROOT_CLEANUP_ERROR_CODE,
    CHROOT_CLEANUP_NEXT_ACTION,
    CONTROLLED_GATE_ERROR_CODE,
    CONTROLLED_GATE_NEXT_ACTION,
    ISOHYBRID_ERROR_CODE,
    ISOHYBRID_NEXT_ACTION,
    ZSYNC_STALE_ERROR_CODE,
    ZSYNC_STALE_NEXT_ACTION,
    analyze_auto_build_gate,
    build_controlled_build_contract,
    build_controlled_operator_build_plan,
    classify_rescue_iso_build_attempt,
)


class RescueIsoBuildResultClassificationTests(unittest.TestCase):
    def test_chroot_cleanup_maps_not_to_isohybrid(self) -> None:
        log = (
            "rm: das Entfernen von 'chroot/proc/1/status' ist nicht möglich: Vorgang nicht zulässig\n"
            "P: Begin unmounting filesystems...\n"
            "chroot: failed to run command '/usr/bin/env': No such file or directory\n"
            "LB_EXIT=1\n"
        )
        result = classify_rescue_iso_build_attempt(
            run_data={"exit_code": 1},
            result_data={"exit_code": 1, "iso_created": False, "usb_write_performed": False},
            combined_log_text=log,
        )
        self.assertEqual(result["error_code"], CHROOT_CLEANUP_ERROR_CODE)
        self.assertEqual(result["next_action"], CHROOT_CLEANUP_NEXT_ACTION)
        self.assertNotEqual(result["error_code"], ISOHYBRID_ERROR_CODE)

    def test_zsync_stale_with_iso_maps_to_zsync_stale_review(self) -> None:
        log = (
            "247380 extents written (483 MB)\n"
            "xz: binary.hybrid.iso.zsync.xz: Die Datei existiert bereits\n"
            "LB_EXIT=1\n"
        )
        result = classify_rescue_iso_build_attempt(
            run_data={"exit_code": 1},
            result_data={"exit_code": 1, "iso_created": True, "usb_write_performed": False},
            combined_log_text=log,
        )
        self.assertEqual(result["error_code"], ZSYNC_STALE_ERROR_CODE)
        self.assertEqual(result["next_action"], ZSYNC_STALE_NEXT_ACTION)
        self.assertEqual(result["result_status"], "review_required")
        self.assertTrue(result["iso_created"])

    def test_isohybrid_not_found_maps_to_isohybrid_error(self) -> None:
        result = classify_rescue_iso_build_attempt(
            run_data={"exit_code": 127},
            result_data={"exit_code": 127, "iso_created": False, "usb_write_performed": False},
            combined_log_text="231515 extents written (452 MB)\nbinary.sh: 5: isohybrid: not found\n",
        )
        self.assertEqual(result["result_status"], "failed")
        self.assertEqual(result["error_code"], ISOHYBRID_ERROR_CODE)
        self.assertEqual(result["next_action"], ISOHYBRID_NEXT_ACTION)
        self.assertFalse(result["iso_created"])

    def test_controlled_gate_message_maps_to_blocked_gate_error(self) -> None:
        result = classify_rescue_iso_build_attempt(
            run_data={
                "command": 'PATH="$(git rev-parse --show-toplevel)/build/rescue/tool-compat/bin:$PATH" lb build',
                "started_at": "2026-05-26T19:09:23+00:00",
                "exit_code": 20,
            },
            result_data={
                "result_status": "failed",
                "exit_code": 20,
                "iso_created": False,
                "usb_write_performed": False,
                "errors": ["failed_live_build_config"],
            },
            combined_log_text="Use controlled gate before running lb build.\n",
        )
        self.assertEqual(result["result_status"], "blocked")
        self.assertEqual(result["error_code"], CONTROLLED_GATE_ERROR_CODE)
        self.assertNotEqual(result["error_code"], "failed_live_build_config")
        self.assertFalse(result["iso_created"])
        self.assertFalse(result["usb_write_performed"])
        self.assertEqual(result["next_action"], CONTROLLED_GATE_NEXT_ACTION)
        self.assertTrue(result["direct_lb_build_blocked"])

    def test_controlled_build_contract_marks_direct_lb_build_as_forbidden(self) -> None:
        triage = analyze_auto_build_gate(
            auto_build_text='#!/bin/sh\necho "Use controlled gate before running lb build."\nexit 20\n',
            logging_wrapper_text=(
                '#!/usr/bin/env bash\n'
                'if [[ "${1:-}" != "--operator-confirm-build" ]]; then exit 20; fi\n'
                'env PATH="${PATH_PREFIX}:${PATH}" ./auto/config\n'
                'sudo env PATH="${PATH_PREFIX}:${PATH}" lb build noauto\n'
            ),
            runbook_text="sudo env PATH=\"/repo/build/rescue/tool-compat/bin:$PATH\" lb build noauto\n",
        )
        contract = build_controlled_build_contract(triage)
        self.assertEqual(contract["contract_status"], "ready")
        self.assertIn("lb build", contract["forbidden_invocations"])
        self.assertFalse(contract["usb_write_allowed"])
        self.assertEqual(contract["supported_target_architecture"], "amd64")
        self.assertEqual(contract["unsupported_targets"], ["i386", "arm64", "armhf"])

    def test_controlled_build_plan_contains_no_bypass_and_keeps_usb_blocked(self) -> None:
        triage = analyze_auto_build_gate(
            auto_build_text='#!/bin/sh\necho "Use controlled gate before running lb build."\nexit 20\n',
            logging_wrapper_text=(
                '#!/usr/bin/env bash\n'
                'if [[ "${1:-}" != "--operator-confirm-build" ]]; then exit 20; fi\n'
                'env PATH="${PATH_PREFIX}:${PATH}" ./auto/config\n'
                'sudo env PATH="${PATH_PREFIX}:${PATH}" lb build noauto\n'
            ),
            runbook_text="sudo env PATH=\"/repo/build/rescue/tool-compat/bin:$PATH\" lb build noauto\n",
        )
        contract = build_controlled_build_contract(triage)
        plan = build_controlled_operator_build_plan(contract)
        joined_steps = "\n".join(plan["exact_operator_steps"])
        self.assertEqual(plan["plan_status"], "ready_for_operator")
        self.assertNotIn("delete auto/build", joined_steps.lower())
        self.assertNotIn("comment out", joined_steps.lower())
        self.assertFalse(plan["usb_write_allowed"])
        self.assertEqual(plan["target_architecture"], "amd64")

    def test_unclear_wrapper_keeps_plan_in_review_required(self) -> None:
        triage = analyze_auto_build_gate(
            auto_build_text='#!/bin/sh\necho "Use controlled gate before running lb build."\nexit 20\n',
            logging_wrapper_text='#!/usr/bin/env bash\nsudo lb build noauto\n',
            runbook_text="sudo lb build noauto\n",
        )
        contract = build_controlled_build_contract(triage)
        plan = build_controlled_operator_build_plan(contract)
        self.assertEqual(contract["contract_status"], "review_required")
        self.assertEqual(plan["plan_status"], "review_required")


if __name__ == "__main__":
    unittest.main()
