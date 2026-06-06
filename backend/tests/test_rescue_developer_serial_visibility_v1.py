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
            r"(?:.*\n)*?"
            r"  LIVE_BOOTAPPEND='([^']+)'\nfi\n\nwrite_text_file \"\$\{BUILD_ROOT\}/auto/config\"",
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

    def test_prepare_archive_areas_include_non_free_firmware(self) -> None:
        text = _read(PREP)
        self.assertRegex(
            text,
            r"--archive-areas 'main contrib non-free-firmware'",
            "archive-areas must be a single quoted lb config argument",
        )
        self.assertRegex(
            text,
            r"--parent-archive-areas 'main contrib non-free-firmware'",
            "parent-archive-areas must be a single quoted lb config argument",
        )

    def test_prepare_parent_debian_archive_lists(self) -> None:
        text = _read(PREP)
        self.assertIn("config/archives/debian.list.chroot", text)
        self.assertIn("bookworm main contrib non-free-firmware", text)
        self.assertIn("bookworm-updates main contrib non-free-firmware", text)

    def test_validate_requires_non_free_firmware_archive_areas(self) -> None:
        validate = _REPO / "scripts/rescue-live/validate-controlled-live-build-tree.sh"
        text = _read(validate)
        self.assertIn("debian.list.chroot", text)
        self.assertIn("parent-archive-areas", text)
        self.assertIn("RESCUE-ISO-PARENT-ARCHIVE-AREAS-001", text)
        self.assertIn("RESCUE-ISO-CHROOT-SOURCES-NONFREE-FIRMWARE-MISSING-001", text)
        self.assertIn("RESCUE-ISO-FIRMWARE-APT-SOURCE-INCOMPLETE-001", text)
        self.assertIn("RESCUE-ISO-FIRMWARE-APT-COMPONENT-001", text)
        self.assertIn("RESCUE-ISO-NETWORKMANAGER-MISSING-001", text)
        self.assertIn("RESCUE-ISO-SERIAL-MARKER-001", text)
        self.assertIn("--initsystem systemd", text)

    def test_controlled_build_msi_firmware_packages_in_prepare(self) -> None:
        text = _read(PREP)
        for pkg in (
            "firmware-iwlwifi",
            "firmware-intel-sound",
            "wireless-regdb",
            "network-manager",
            "wpasupplicant",
        ):
            self.assertIn(pkg, text, f"prepare must list {pkg} for MSI rescue WLAN/BT")

    def test_prepare_initsystem_systemd(self) -> None:
        text = _read(PREP)
        self.assertIn("--initsystem systemd \\", text)

    def test_prepare_serial_marker_unit_in_tree(self) -> None:
        text = _read(PREP)
        self.assertIn("write_rescue_serial_boot_markers_service", text)
        self.assertIn("ConditionVirtualization=qemu", text)
        self.assertNotIn("TTYPath=/dev/ttyS0", text.split("write_rescue_serial_boot_markers_service")[1].split("EOF")[0])

    def test_prepare_network_manager_safety_hook(self) -> None:
        text = _read(PREP)
        self.assertIn("015-ensure-network-manager.hook.chroot", text)
        self.assertIn("systemctl enable NetworkManager.service", text)

    def test_validate_checks_msi_firmware_packages(self) -> None:
        validate = _REPO / "scripts/rescue-live/validate-controlled-live-build-tree.sh"
        text = _read(validate)
        for pkg in ("firmware-iwlwifi", "firmware-intel-sound", "wireless-regdb", "network-manager"):
            self.assertIn(f"'{pkg}'", text, f"validator must grep {pkg}")

    def test_serial_marker_scripts_exist(self) -> None:
        marker = QEMU_PROFILE / "includes.chroot/usr/local/sbin/setuphelfer-serial-boot-markers.sh"
        svc = QEMU_PROFILE / "includes.chroot/etc/systemd/system/setuphelfer-serial-boot-markers.service"
        self.assertTrue(marker.is_file())
        self.assertTrue(svc.is_file())
        svc_text = _read(svc)
        self.assertIn("SETUPHELFER_BOOT_MARKER_START", _read(marker))
        self.assertIn("ConditionVirtualization=qemu", svc_text)
        self.assertNotIn("TTYPath=/dev/ttyS0", svc_text)

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
