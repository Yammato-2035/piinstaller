"""PI-RS-MSI-GUI-002 disable GUI under MSI compat tests."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMON = REPO_ROOT / "scripts/rescue-live/image/setuphelfer-rescue-common.sh"


class MsiGui002DisableGuiTests(unittest.TestCase):
    def test_central_helpers_present(self) -> None:
        text = COMMON.read_text(encoding="utf-8")
        for marker in (
            "setuphelfer_rescue_should_disable_gui_for_msi_compat",
            "setuphelfer_rescue_write_gui_availability_status",
            "setuphelfer_rescue_gui_disabled_message",
            "setuphelfer_rescue_write_gui_blocked_msi_status",
        ):
            self.assertIn(marker, text)

    def test_gui_availability_json_shape(self) -> None:
        text = COMMON.read_text(encoding="utf-8")
        self.assertIn("gui_available", text)
        self.assertIn("openvt_allowed", text)
        self.assertIn("chvt_allowed", text)
        self.assertIn("startx_allowed", text)
        self.assertIn("use_text_mode", text)

    def test_msi_detection_requires_compat_and_nomodeset_or_dmi(self) -> None:
        text = COMMON.read_text(encoding="utf-8")
        self.assertIn("setuphelfer_rescue_cmdline_has_nomodeset", text)
        self.assertIn("setuphelfer_rescue_dmi_suggests_msi_ge63", text)
        self.assertIn("setuphelfer_rescue_msi_compat_active", text)


if __name__ == "__main__":
    unittest.main()
