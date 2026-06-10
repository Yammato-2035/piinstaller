"""Rescue UI launcher executable contract tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from rescue.rescue_ui_launcher_contract import (
    EXPECTED_FALLBACK_STATUS,
    build_expected_fallback_status_json,
    evaluate_workspace_launcher_contract,
    simulate_fallback_status_contract,
    validate_expected_fallback_status_payload,
    validate_launcher_script_contract,
)

REPO = Path(__file__).resolve().parents[2]
LAUNCHER = REPO / "scripts/rescue-live/image/setuphelfer-rescue-ui-launch"


class RescueUiLauncherContractTests(unittest.TestCase):
    def test_launcher_workspace_contract(self) -> None:
        text = LAUNCHER.read_text(encoding="utf-8")
        result = validate_launcher_script_contract(text)
        self.assertTrue(result["contract_ok"], result["errors"])

    def test_expected_fallback_status_shape(self) -> None:
        payload = build_expected_fallback_status_json()
        for key, value in EXPECTED_FALLBACK_STATUS.items():
            self.assertEqual(payload.get(key), value)
        self.assertEqual(validate_expected_fallback_status_payload(payload), [])

    def test_simulate_fallback_status_contract(self) -> None:
        result = simulate_fallback_status_contract()
        self.assertTrue(result["contract_ok"])

    def test_no_ready_on_url_only(self) -> None:
        text = LAUNCHER.read_text(encoding="utf-8")
        self.assertNotIn('"status": "ready"', text.split("url_only")[0] if "url_only" in text else text)

    def test_workspace_full_contract(self) -> None:
        ws = evaluate_workspace_launcher_contract(REPO)
        self.assertTrue(ws["contract_ok"], ws)


if __name__ == "__main__":
    unittest.main()
