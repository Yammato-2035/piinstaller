"""PI-RS-ASUS-AUTO-WIN11-LOG-007: autonomous G513QM setup-log capture gate + copy."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Sequence
from unittest import mock

_BACKEND = Path(__file__).resolve().parent.parent
_REPO = _BACKEND.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from core import rescue_auto_win11_setup_log_capture as auto  # noqa: E402
from core import rescue_hardware_discovery_capture as hdc  # noqa: E402


class AutoWin11GateTests(unittest.TestCase):
    def test_skips_non_g513qm(self) -> None:
        r = auto.evaluate_auto_win11_setup_log_gate(
            cmdline="setuphelfer_rescue=1 setuphelfer_start_assistant=1",
            dmi={"board_name": "MS-16P6", "product_name": "GE63"},
            done_marker=Path("/tmp/does-not-exist-auto-win11-done"),
        )
        self.assertFalse(r["should_run"])
        self.assertEqual(r["reason"], "not_g513qm")

    def test_runs_on_g513qm_rescue(self) -> None:
        r = auto.evaluate_auto_win11_setup_log_gate(
            cmdline="setuphelfer_rescue=1 setuphelfer_start_assistant=1",
            dmi={"board_name": "G513QM", "product_name": "ROG Strix G513QM"},
            done_marker=Path("/tmp/does-not-exist-auto-win11-done"),
        )
        self.assertTrue(r["should_run"])
        self.assertTrue(r["auto_gabriel_bind"])
        self.assertFalse(r["write_allowed"])

    def test_blocks_msi_lab(self) -> None:
        r = auto.evaluate_auto_win11_setup_log_gate(
            cmdline="setuphelfer_rescue=1 setuphelfer_msi_lab_auto=1",
            dmi={"board_name": "G513QM", "product_name": "ROG Strix G513QM"},
            done_marker=Path("/tmp/does-not-exist-auto-win11-done"),
        )
        self.assertFalse(r["should_run"])
        self.assertIn("msi_lab_or_e2e_active", r["reasons"])


class WindowsLogCopyTests(unittest.TestCase):
    def test_collect_copies_panther(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mp = root / "mnt"
            panther = mp / "Windows" / "Panther"
            panther.mkdir(parents=True)
            (panther / "setuperr.log").write_text("Error 0x8007045d storage driver\n", encoding="utf-8")
            copy_root = root / "copy"
            export_root = root / "export"

            def run(cmd: Sequence[str], timeout: float = 60.0) -> tuple[int, str, str]:
                if cmd[0] == "modprobe":
                    return 0, "", ""
                if cmd[0] in {"mount", "ntfs-3g", "mount.ntfs-3g"}:
                    return 0, "", ""
                if cmd[0] == "findmnt":
                    return 0, "ro,norecover\n", ""
                if cmd[0] == "umount":
                    return 0, "", ""
                return 1, "", "unexpected"

            with mock.patch.object(hdc, "scan_windows_setup_evidence") as scan:
                scan.return_value = {
                    "status": "ok",
                    "files": [{"path": str(panther / "setuperr.log"), "error_classes": ["storage_driver"]}],
                    "error_classes": ["storage_driver"],
                }
                # Pretend mount succeeds and leaves files under work_root/ntfs-ro-0
                work = root / "work"
                fake_mp = work / "ntfs-ro-0"
                fake_mp.mkdir(parents=True)
                fake_panther = fake_mp / "Windows" / "Panther"
                fake_panther.mkdir(parents=True)
                (fake_panther / "setuperr.log").write_text("Error 0x8007045d storage driver\n", encoding="utf-8")
                scan.return_value = {
                    "status": "ok",
                    "files": [
                        {
                            "path": str(fake_panther / "setuperr.log"),
                            "error_classes": ["storage_driver"],
                        }
                    ],
                    "error_classes": ["storage_driver"],
                }
                out = hdc.collect_windows_setup_logs(
                    ntfs_sources=["/dev/nvme0n1p2"],
                    work_root=work,
                    run=run,
                    copy_root=copy_root,
                    export_root=export_root,
                )
            self.assertTrue(out["panther_found"])
            self.assertEqual(out["copied_file_count"], 1)
            self.assertTrue((copy_root / "Windows" / "Panther" / "setuperr.log").is_file())
            self.assertTrue((export_root / "Windows" / "Panther" / "setuperr.log").is_file())
            self.assertEqual(out["files"][0]["copy_status"], "copied")


class PayloadFlagTests(unittest.TestCase):
    def test_payload_007(self) -> None:
        cfg = json.loads((_REPO / "config/rescue_payload_version.json").read_text(encoding="utf-8"))
        self.assertEqual(cfg["rescue_payload_version"], "1.10.4.0")
        self.assertEqual(cfg["previous_rescue_payload_version"], "1.10.3.1")
        self.assertTrue(cfg.get("pi_rs_asus_auto_win11_log_007"))


if __name__ == "__main__":
    unittest.main()
