"""Read-only rescue partitions TUI preview tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]


class RescuePartitionsTuiPreviewTests(unittest.TestCase):
    def test_preview_write_allowed_always_false(self) -> None:
        from rescue.rescue_partitions_tui_preview import build_partitions_tui_preview

        fake = {
            "blockdevices": [
                {
                    "name": "nvme0n1",
                    "path": "/dev/nvme0n1",
                    "type": "disk",
                    "size": 512_000_000_000,
                    "model": "TEST NVME",
                    "tran": "nvme",
                    "rm": False,
                    "children": [
                        {
                            "name": "nvme0n1p1",
                            "path": "/dev/nvme0n1p1",
                            "type": "part",
                            "size": 500_000_000,
                            "fstype": "vfat",
                            "label": "EFI",
                        }
                    ],
                }
            ]
        }
        with mock.patch(
            "rescue.rescue_partitions_tui_preview._lsblk_json",
            return_value=fake,
        ):
            preview = build_partitions_tui_preview()
        self.assertFalse(preview["write_allowed"])
        self.assertFalse(preview["partition_rewritten"])
        self.assertEqual(preview["disk_count"], 1)
        self.assertEqual(preview["partition_count"], 1)
        self.assertIn("parted", preview["safety"]["forbidden_ops"])

    def test_format_message_mentions_readonly(self) -> None:
        from rescue.rescue_partitions_tui_preview import (
            build_partitions_tui_preview,
            format_partitions_tui_message,
        )

        with mock.patch(
            "rescue.rescue_partitions_tui_preview._lsblk_json",
            return_value={"blockdevices": []},
        ):
            msg = format_partitions_tui_message(build_partitions_tui_preview())
        self.assertIn("nur Lesen", msg)
        self.assertIn("Schreiben erlaubt: False", msg)
        self.assertIn("write_allowed=false", msg)

    def test_write_json(self) -> None:
        from rescue.rescue_partitions_tui_preview import (
            build_partitions_tui_preview,
            write_partitions_preview_json,
        )

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "p.json"
            with mock.patch(
                "rescue.rescue_partitions_tui_preview._lsblk_json",
                return_value={"blockdevices": []},
            ):
                write_partitions_preview_json(path, build_partitions_tui_preview())
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertFalse(data["write_allowed"])

    def test_tui_menu_has_partitions_entry(self) -> None:
        text = (REPO / "scripts/rescue-live/image/setuphelfer-rescue-tui.sh").read_text(encoding="utf-8")
        self.assertIn('_tui_run_partitions', text)
        self.assertIn('"partitions"', text)
        self.assertIn("Partitionshelfer (nur Lesen)", text)

    def test_autocapture_calls_partitions_preview(self) -> None:
        text = (
            REPO / "scripts/rescue-live/image/setuphelfer-rescue-tui-baseline-autocapture.sh"
        ).read_text(encoding="utf-8")
        self.assertIn("rescue_partitions_tui_preview", text)
        self.assertIn("partitions-preview.json", text)
        self.assertIn("setuphelfer_rescue_backend_python", text)


if __name__ == "__main__":
    unittest.main()
