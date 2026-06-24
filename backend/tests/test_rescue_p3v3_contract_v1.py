"""RS-P3V.3 boot splash contract checks (MSI discovery/splash fix scope)."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RESCUE_SRC = REPO / "frontend/src/rescue"


class RescueP3V3ContractTests(unittest.TestCase):
    def test_boot_splash_status_cards(self) -> None:
        splash = (RESCUE_SRC / "RescueBootSplash.tsx").read_text(encoding="utf-8")
        self.assertIn("rescue-boot-status-list", splash)
        self.assertIn("Datenträger werden erkannt", splash)
        x11 = (REPO / "scripts/rescue-live/image/setuphelfer-rescue-x11-hold").read_text(encoding="utf-8")
        self.assertIn("Datenträger werden erkannt", x11)


if __name__ == "__main__":
    unittest.main()
