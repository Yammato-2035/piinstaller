"""Tests for PI-RS-MSI-AUTO-EVIDENCE-001."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.rescue_fat32_esp_usb_writer import generate_fat32_esp_grub_cfg  # noqa: E402
from core.rescue_msi_lab_auto_boot import (  # noqa: E402
    MSI_COMPAT_MENU_TITLE,
    MSI_LAB_CMDLINE_FLAGS,
    patch_grub_cfg_for_msi_lab_auto_boot,
)
from core.rescue_msi_lab_evidence_eval import evaluate_msi_lab_evidence  # noqa: E402


class MsiLabAutoBootTests(unittest.TestCase):
    def test_generate_grub_lab_auto_msi_first_entry(self) -> None:
        cfg = generate_fat32_esp_grub_cfg(lab_auto_msi_boot=True)
        self.assertIn("set timeout=3", cfg)
        self.assertIn("set timeout_style=countdown", cfg)
        self.assertIn(MSI_LAB_CMDLINE_FLAGS.split()[0], cfg)
        self.assertIn("setuphelfer_auto_discovery=1", cfg)
        self.assertIn("setuphelfer_msi_e2e_auto=0", cfg)
        first_menu = cfg.index('menuentry "Setuphelfer MSI/NVIDIA')
        first_text = cfg.index('menuentry "Setuphelfer starten - sicherer Textmodus')
        self.assertLess(first_menu, first_text)

    def test_patch_existing_grub_adds_discovery_flag_when_lab_auto_present(self) -> None:
        base = generate_fat32_esp_grub_cfg()
        base = patch_grub_cfg_for_msi_lab_auto_boot(base)
        self.assertIn("setuphelfer_auto_discovery=1", base)
        self.assertIn("setuphelfer_msi_e2e_auto=0", base)
        patched = patch_grub_cfg_for_msi_lab_auto_boot(base)
        self.assertIn("setuphelfer_auto_discovery=1", patched)
        self.assertNotIn("setuphelfer_msi_e2e_auto=1", patched)

    def test_patch_existing_grub_for_lab_auto(self) -> None:
        base = generate_fat32_esp_grub_cfg()
        patched = patch_grub_cfg_for_msi_lab_auto_boot(base)
        self.assertIn("setuphelfer_msi_lab_auto=1", patched)
        self.assertIn("set timeout=3", patched)
        first_msi = patched.index(f'menuentry "{MSI_COMPAT_MENU_TITLE}"')
        first_text = patched.index('menuentry "Setuphelfer starten - sicherer Textmodus"')
        self.assertLess(first_msi, first_text)


class MsiLabEvidenceEvalTests(unittest.TestCase):
    def test_evaluate_passes_with_tui_and_late_uptime(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ev = root / "msi-rs011b"
            ev.mkdir()
            (ev / "boot-timeline.jsonl").write_text(
                json.dumps({"phase": "tui_mode_selected", "status": "ok"}) + "\n",
                encoding="utf-8",
            )
            (ev / "late-evidence-auto-test.txt").write_text("ok\n", encoding="utf-8")
            ownership = root / "console-ownership.json"
            ownership.write_text(
                json.dumps(
                    {
                        "owner": "tui",
                        "lifecycle_state": "tui_owned",
                        "boot_progress_write_allowed": False,
                    }
                ),
                encoding="utf-8",
            )
            result = evaluate_msi_lab_evidence(
                evidence_dir=ev,
                console_ownership_path=ownership,
                timeline_path=ev / "boot-timeline.jsonl",
                uptime_sec=130.0,
            )
            self.assertEqual(result["result_status"], "passed")
            self.assertTrue(result["capture_after_120s"])
            self.assertTrue(result["tui_owned"])

    def test_evaluate_fails_early_uptime(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ev = root / "msi-rs011b"
            ev.mkdir()
            ownership = root / "console-ownership.json"
            ownership.write_text(json.dumps({"owner": "boot_progress"}), encoding="utf-8")
            result = evaluate_msi_lab_evidence(
                evidence_dir=ev,
                console_ownership_path=ownership,
                uptime_sec=10.0,
            )
            self.assertEqual(result["result_status"], "failed")
            self.assertIn("capture_uptime_below_120s", result["errors"])

    def test_lab_auto_unattended_skips_tui_errors_when_late_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ev = root / "msi-rs011b"
            ev.mkdir()
            (ev / "late-evidence-auto-test.txt").write_text("ok\n", encoding="utf-8")
            ownership = root / "console-ownership.json"
            ownership.write_text(json.dumps({"owner": "boot_progress"}), encoding="utf-8")
            result = evaluate_msi_lab_evidence(
                evidence_dir=ev,
                console_ownership_path=ownership,
                uptime_sec=150.0,
                lab_auto_unattended=True,
            )
            self.assertNotIn("console_owner_not_tui", result["errors"])
            self.assertNotIn("tui_mode_selected_missing", result["errors"])
            self.assertEqual(result["result_status"], "passed")


if __name__ == "__main__":
    unittest.main()
