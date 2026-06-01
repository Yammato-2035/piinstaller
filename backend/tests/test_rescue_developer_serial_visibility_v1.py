"""Static tests for developer-qemu serial boot visibility configuration."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
PREP = _REPO / "scripts/rescue-live/prepare-controlled-live-build-tree.sh"
QEMU_PROFILE = _REPO / "build/rescue/profiles/developer-qemu"
FLEET_FINISH = _REPO / "scripts/rescue-live/fleet-session-api.sh"
WRAPPER = _REPO / "scripts/rescue-live/run-qemu-developer-iso-smoke.sh"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class RescueDeveloperSerialVisibilityTests(unittest.TestCase):
    def test_developer_qemu_bootappend_in_prepare(self) -> None:
        text = _read(PREP)
        m = re.search(
            r'if \[\[ "\$\{RESCUE_BUILD_PROFILE\}" == "developer-qemu" \]\]; then\n'
            r"(?:  #.*\n)?  LIVE_BOOTAPPEND='([^']+)'\nfi\n\nwrite_text_file \"\$\{BUILD_ROOT\}/auto/config\"",
            text,
        )
        self.assertIsNotNone(m, "developer-qemu LIVE_BOOTAPPEND block")
        append = m.group(1)
        self.assertIn("console=tty0", append)
        self.assertIn("console=ttyS0,115200n8", append)
        self.assertNotIn("quiet", append)
        self.assertNotIn("splash", append)
        self.assertIn("loglevel=7", append)
        self.assertIn("systemd.log_level=debug", append)

    def test_serial_marker_scripts_exist(self) -> None:
        marker = QEMU_PROFILE / "includes.chroot/usr/local/sbin/setuphelfer-serial-boot-markers.sh"
        svc = QEMU_PROFILE / "includes.chroot/etc/systemd/system/setuphelfer-serial-boot-markers.service"
        self.assertTrue(marker.is_file())
        self.assertTrue(svc.is_file())
        self.assertIn("SETUPHELFER_BOOT_MARKER_START", _read(marker))

    def test_autopilot_serial_markers(self) -> None:
        text = _read(
            QEMU_PROFILE / "includes.chroot/usr/local/sbin/setuphelfer-qemu-smoke-autopilot.sh"
        )
        for token in (
            "SETUPHELFER_AUTOPILOT_START",
            "SETUPHELFER_DEVSERVER_AGENT_START",
            "SETUPHELFER_DEVSERVER_AGENT_REPORT_ATTEMPT",
        ):
            self.assertIn(token, text)

    def test_fleet_finish_payload_serial_and_kvm(self) -> None:
        text = _read(FLEET_FINISH)
        self.assertIn("FLEET_SERIAL_PATH", text)
        self.assertIn('"exists": serial_exists', text)
        self.assertIn("FLEET_ACCELERATION", text)
        self.assertIn("kvm_enabled", text)

    def test_wrapper_exports_finish_telemetry(self) -> None:
        text = _read(WRAPPER)
        self.assertIn("FLEET_SERIAL_PATH", text)
        self.assertIn("FLEET_ACCELERATION", text)
        self.assertIn("classification_hint_serial_empty_boot_unknown", text)


if __name__ == "__main__":
    unittest.main()
