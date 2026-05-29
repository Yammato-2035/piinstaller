from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.rescue_vm_boot_smoke import classify_visual_live_functional_validation  # noqa: E402


class RescueIsoVisualLiveFunctionalValidationTests(unittest.TestCase):
    def test_prepared_not_executed_without_freigabe(self) -> None:
        result = classify_visual_live_functional_validation(
            visual_vm_test_executed=False,
            operator_authorized=False,
        )
        self.assertEqual(result["classification"], "visual_live_functional_prepared_not_executed")
        self.assertEqual(result["rescue_runtime_functional_status"], "yellow")

    def test_full_success(self) -> None:
        result = classify_visual_live_functional_validation(
            visual_vm_test_executed=True,
            operator_authorized=True,
            operator_output_provided=True,
            live_system_started=True,
            login_prompt_seen=True,
            login_user_live_success=True,
            bundle_path_present=True,
            backend_service_active=True,
            backend_version_ok=True,
            keyboard_de=True,
            locale_de=True,
            hostname_setuphelfer_rescue=True,
        )
        self.assertEqual(result["classification"], "live_boot_success_login_ok_backend_ok")
        self.assertEqual(result["rescue_runtime_functional_status"], "partial_green")

    def test_backend_failed(self) -> None:
        result = classify_visual_live_functional_validation(
            visual_vm_test_executed=True,
            operator_authorized=True,
            operator_output_provided=True,
            live_system_started=True,
            login_prompt_seen=True,
            login_user_live_success=True,
            bundle_path_present=True,
            backend_service_active=False,
            keyboard_de=True,
            locale_de=True,
        )
        self.assertEqual(result["classification"], "live_boot_success_backend_failed")


if __name__ == "__main__":
    unittest.main()
