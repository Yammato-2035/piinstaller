"""Tests for rescue start assistant productization (workspace scripts)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
IMAGE = REPO / "scripts" / "rescue-live" / "image"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class RescueStartAssistantTests(unittest.TestCase):
    def test_scripts_bash_syntax(self) -> None:
        for name in (
            "setuphelfer-rescue-start-assistant",
            "setuphelfer-rescue-network-onboarding",
            "setuphelfer-rescue-disk-discovery",
            "setuphelfer-rescue-media-check",
        ):
            proc = subprocess.run(["bash", "-n", str(IMAGE / name)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, f"{name}: {proc.stderr}")

    def test_disk_discovery_classifies_rescue_stick(self) -> None:
        mod = _load_module("disk_discovery", IMAGE / "setuphelfer-rescue-disk-discovery.py")
        devices = [
            {
                "name": "sdb1",
                "path": "/dev/sdb1",
                "type": "part",
                "size": 683671552,
                "label": "SETUPHELFER_RESCUE",
                "fstype": "iso9660",
                "mountpoints": ["/run/live/medium"],
                "tran": "usb",
                "rm": True,
            }
        ]
        cls = mod.classify_node(devices[0], {"sdb", "sdb1"})
        self.assertEqual(cls, "rescue_stick")

    def test_disk_discovery_recommends_backup_before_repair(self) -> None:
        mod = _load_module("disk_discovery2", IMAGE / "setuphelfer-rescue-disk-discovery.py")
        devices = [
            {"classification": "windows_system", "type": "part", "path": "/dev/nvme0n1p4"},
            {"classification": "rescue_stick", "type": "part", "path": "/dev/sdb1"},
        ]
        rec = mod.recommend_action(devices, media_stable=True)
        self.assertEqual(rec["recommended_next_action"], "backup_before_repair_or_install")

    def test_plan_builder_blocks_unstable_media(self) -> None:
        mod = _load_module("plan_builder", IMAGE / "setuphelfer-rescue-plan-builder.py")
        plans = mod.build_plans({"devices": []}, {"media_check": {"live_media_runtime_stable": False}, "selected_action": "repair"})
        self.assertFalse(plans.get("execution_allowed", False))
        self.assertEqual(plans.get("blocked_reason"), "live_media_unstable")

    def test_plan_builder_repair_blocked_without_execution(self) -> None:
        mod = _load_module("plan_builder2", IMAGE / "setuphelfer-rescue-plan-builder.py")
        plans = mod.build_plans(
            {"devices": [{"classification": "linux_system", "path": "/dev/nvme1n1"}]},
            {"media_check": {"live_media_runtime_stable": True}, "selected_action": "repair"},
        )
        self.assertIn("repair_plan", plans)
        self.assertEqual(plans["repair_plan"]["execution"], "blocked_until_backup_acknowledged")

    def test_boot_menu_snippet_present(self) -> None:
        snippet = (IMAGE / "setuphelfer-rescue-boot-menu-snippet.cfg").read_text(encoding="utf-8")
        self.assertIn("label setuphelfer-rescue-default", snippet)
        self.assertIn("Setuphelfer Rettung starten", snippet)
        self.assertIn("pci=noaer", snippet)

    def test_telemetry_push_no_inline_heredoc_json(self) -> None:
        text = (IMAGE / "setuphelfer-rescue-telemetry-push").read_text(encoding="utf-8")
        self.assertNotIn('json.loads("""', text)
        self.assertIn("setuphelfer-rescue-telemetry-build-payload.py", text)

    def test_common_wifi_menu_uses_index_not_raw_ssid_tag(self) -> None:
        text = (IMAGE / "setuphelfer-rescue-common.sh").read_text(encoding="utf-8")
        self.assertIn("--passwordbox", text)
        self.assertIn("_entries[_idx]", text)

    def test_start_assistant_service_unit_autostart_fields(self) -> None:
        prepare = (REPO / "scripts" / "rescue-live" / "prepare-controlled-live-build-tree.sh").read_text(encoding="utf-8")
        self.assertIn("ConditionKernelCommandLine=setuphelfer_start_assistant=1", prepare)
        self.assertIn("TTYPath=/dev/tty1", prepare)
        self.assertIn("StandardInput=tty", prepare)
        self.assertIn("StandardOutput=tty", prepare)
        self.assertIn("Environment=TERM=linux", prepare)
        self.assertIn("TTYVTDisallocate=yes", prepare)
        self.assertIn("getty@tty1.service.d/setuphelfer-rescue.conf", prepare)

    def test_start_assistant_writes_status_path(self) -> None:
        text = (IMAGE / "setuphelfer-rescue-start-assistant").read_text(encoding="utf-8")
        self.assertIn("setuphelfer_rescue_start_assistant_status_path", text)
        self.assertIn("setuphelfer_rescue_write_start_assistant_status", text)
        self.assertIn("setuphelfer_rescue_cmdline_has_start_assistant", text)
        self.assertIn("setuphelfer_rescue_show_start_assistant_fallback", text)
        common = (IMAGE / "setuphelfer-rescue-common.sh").read_text(encoding="utf-8")
        self.assertIn("start-assistant-status.json", common)

    def test_start_assistant_status_has_no_password_fields(self) -> None:
        text = (IMAGE / "setuphelfer-rescue-start-assistant").read_text(encoding="utf-8")
        self.assertNotIn("password", text.lower().replace("passwordbox", ""))
        self.assertIn('"secrets_exposed": false', text)


if __name__ == "__main__":
    unittest.main()
