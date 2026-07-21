"""Tests for auto-E2E GUI status helper (PI-RS-MSI-GUI-AUTO-BVR-001)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.rescue_auto_e2e_gui_status import (  # noqa: E402
    build_auto_e2e_gui_status,
    msi_e2e_auto_active,
)
from core.rescue_physical_e2e_auto_e2e_state import init_auto_e2e_state, update_auto_e2e_state  # noqa: E402


class AutoE2eGuiStatusTests(unittest.TestCase):
    def test_msi_e2e_auto_active_flag(self) -> None:
        self.assertTrue(msi_e2e_auto_active("foo setuphelfer_msi_e2e_auto=1 bar"))
        self.assertFalse(msi_e2e_auto_active("setuphelfer_msi_e2e_auto=0"))

    def test_build_status_from_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict("os.environ", {"SETUPHELFER_AUTO_E2E_STATE_DIR": tmp}):
                init_auto_e2e_state(mode="auto_physical_e2e_locked", run_id="run-xyz")
                update_auto_e2e_state(
                    phase="backup_create",
                    status="running",
                    last_progress="Backup läuft",
                )
                payload = build_auto_e2e_gui_status(
                    cmdline="setuphelfer_mode=gui setuphelfer_msi_e2e_auto=1"
                )
                self.assertTrue(payload["active"])
                self.assertEqual(payload["run_id"], "run-xyz")
                self.assertEqual(payload["phase"], "backup_create")
                self.assertEqual(payload["status"], "running")
                self.assertIn("Backup", payload["phase_label_de"])
                self.assertTrue(payload["gui_mode"])


if __name__ == "__main__":
    unittest.main()
