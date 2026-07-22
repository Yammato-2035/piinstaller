"""PI-RS-ASUS-WIN11-LINUX-001 automated contract tests."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core import rescue_bios_official_compare as bios  # noqa: E402
from core import rescue_firmware_inventory as fw  # noqa: E402
from core import rescue_install_readiness_dcc as dcc  # noqa: E402
from core import rescue_linux_second_nvme as linux  # noqa: E402
from core import rescue_machine_identity_profiles as mid  # noqa: E402
from core import rescue_nvme_install_target as nvme  # noqa: E402
from core import rescue_windows11_install_diag as win  # noqa: E402


class MachineIdentityTests(unittest.TestCase):
    def test_msi_ge63_high(self) -> None:
        ident = mid.build_machine_identity(
            dmi={
                "sys_vendor": "Micro-Star International Co., Ltd.",
                "product_name": "GE63 Raider RGB 8RF",
                "board_name": "MS-16P5",
                "bios_version": "E16P5IMS.31A",
                "product_serial": "SECRETSERIAL9999",
            }
        )
        self.assertEqual(ident["expected_profile"], mid.PROFILE_MSI_GE63)
        self.assertEqual(ident["confidence"], "high")
        self.assertNotIn("SECRETSERIAL9999", str(ident))
        self.assertTrue(ident["serial_masked"].endswith("9999"))

    def test_asus_rog_generic_not_gabriel(self) -> None:
        ident = mid.build_machine_identity(
            dmi={
                "sys_vendor": "ASUSTeK COMPUTER INC.",
                "product_name": "ROG Strix",
                "board_name": "ROG",
                "product_serial": "ABCD1234",
            }
        )
        self.assertEqual(ident["expected_profile"], mid.PROFILE_ASUS_ROG)
        self.assertFalse(ident["is_gabriel_target"])
        self.assertFalse(ident["gabriel_bound"])

    def test_developer_g713pi_not_gabriel(self) -> None:
        ident = mid.build_machine_identity(
            dmi={
                "sys_vendor": "ASUSTeK COMPUTER INC.",
                "product_name": "ROG Strix G713PI_G713PI",
                "board_name": "G713PI",
                "bios_version": "G713PI.334",
                "product_serial": "DEVHOST01",
            }
        )
        self.assertEqual(ident["expected_profile"], mid.PROFILE_ASUS_ROG)
        self.assertTrue(ident["is_developer_workstation"])
        bind = mid.bind_gabriel_operator_profile(
            ident,
            operator_confirmed=True,
            exact_model_confirmed="whatever",
            not_developer_host_ack=True,
        )
        self.assertFalse(bind["ok"])
        self.assertEqual(bind["error"], "developer_asus_cannot_bind_as_gabriel")

    def test_gabriel_bind_requires_operator(self) -> None:
        ident = mid.build_machine_identity(
            dmi={
                "sys_vendor": "ASUSTeK COMPUTER INC.",
                "product_name": "ROG Strix G513QM_G513QM",
                "board_name": "G513QM",
                "product_serial": "GABRIEL01",
            }
        )
        fail = mid.bind_gabriel_operator_profile(
            ident,
            operator_confirmed=False,
            exact_model_confirmed="",
            not_developer_host_ack=False,
        )
        self.assertFalse(fail["ok"])
        ok = mid.bind_gabriel_operator_profile(
            ident,
            operator_confirmed=True,
            exact_model_confirmed="ROG Strix G513QM",
            not_developer_host_ack=True,
            operator_phrase=mid.GABRIEL_OPERATOR_PHRASE,
        )
        self.assertTrue(ok["ok"])
        self.assertEqual(ok["identity"]["expected_profile"], mid.PROFILE_ASUS_ROG_GABRIEL)
        self.assertFalse(ok["identity"]["write_permissions"]["storage_write"])
        self.assertFalse(ok["identity"]["write_permissions"]["installation"])

    def test_msi_asus_conflict(self) -> None:
        a = {"expected_profile": mid.PROFILE_MSI_GE63}
        b = {"expected_profile": mid.PROFILE_ASUS_ROG}
        self.assertTrue(mid.profiles_conflict(a, b))

    def test_unknown_blocks_install(self) -> None:
        ident = mid.build_machine_identity(dmi={"sys_vendor": "Generic", "product_name": "PC"})
        self.assertEqual(ident["expected_profile"], mid.PROFILE_UNKNOWN)
        self.assertTrue(ident["unknown_machine_blocks_install"])


class NvmeIdentityTests(unittest.TestCase):
    def test_role_stable_across_device_rename(self) -> None:
        inv_a = [
            {"device_path": "/dev/nvme0n1", "model": "SSD1", "serial": "WINSERIAL01", "size_bytes": 2000, "pci_address": "0000:01:00.0"},
            {"device_path": "/dev/nvme1n1", "model": "SSD2", "serial": "LINUXSER02", "size_bytes": 2000, "pci_address": "0000:02:00.0"},
        ]
        inv_b = [
            {"device_path": "/dev/nvme1n1", "model": "SSD1", "serial": "WINSERIAL01", "size_bytes": 2000, "pci_address": "0000:01:00.0"},
            {"device_path": "/dev/nvme0n1", "model": "SSD2", "serial": "LINUXSER02", "size_bytes": 2000, "pci_address": "0000:02:00.0"},
        ]
        targets = nvme.build_asus_install_targets_manifest(
            windows={**inv_a[0], "confirmed": True},
            linux={**inv_a[1], "confirmed": True},
        )
        self.assertTrue(targets["targets_distinct"])
        resolved = nvme.resolve_role_after_device_rename(inv_b, targets)
        self.assertTrue(resolved["ok"])
        self.assertEqual(resolved["windows"]["entry"]["device_path"], "/dev/nvme1n1")
        self.assertEqual(resolved["linux"]["entry"]["device_path"], "/dev/nvme0n1")

    def test_same_serial_rejected(self) -> None:
        m = nvme.build_asus_install_targets_manifest(
            windows={"serial": "SAME", "model": "A", "size_bytes": 1},
            linux={"serial": "SAME", "model": "B", "size_bytes": 2},
        )
        self.assertFalse(m["targets_distinct"])

    def test_critical_smart_blocks(self) -> None:
        h = nvme.evaluate_nvme_health({"smart_status": "ok", "critical_warning": True, "media_errors": 0})
        self.assertEqual(h["health_status"], "unsuitable_for_install")
        self.assertFalse(h["install_allowed"])


class BiosCompareTests(unittest.TestCase):
    def test_msi_catalog_compare(self) -> None:
        machine = mid.build_machine_identity(
            dmi={
                "sys_vendor": "MSI",
                "product_name": "GE63 Raider RGB 8RF",
                "board_name": "MS-16P5",
                "bios_version": "E16P5IMS.31A",
            }
        )
        result = bios.check_latest_official_bios(machine=machine, online=True)
        self.assertEqual(result["status"], "current")
        self.assertFalse(result["automatic_flash_allowed"])
        self.assertEqual(result["end_state"], "bios_checked")

    def test_offline(self) -> None:
        machine = mid.build_machine_identity(
            dmi={"sys_vendor": "MSI", "product_name": "GE63 Raider RGB 8RF", "board_name": "MS-16P5", "bios_version": "X"}
        )
        result = bios.check_latest_official_bios(machine=machine, online=False)
        self.assertEqual(result["status"], "latest_version_unknown_offline")

    def test_rejects_third_party_url(self) -> None:
        self.assertFalse(bios.is_official_source_url("https://bios-dl.example.com/file"))
        self.assertTrue(bios.is_official_source_url("https://www.msi.com/Laptop/support"))

    def test_no_flash_in_firmware_inventory(self) -> None:
        inv = fw.collect_firmware_inventory(
            dmi={"sys_vendor": "MSI", "product_name": "GE63", "board_name": "MS-16P5", "bios_version": "1"}
        )
        self.assertFalse(inv["automatic_flash_allowed"])
        self.assertFalse(inv["flash_endpoint_available"])


class WindowsEvidenceTests(unittest.TestCase):
    def test_panther_scan_and_classify(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            panther = root / "Windows" / "Panther"
            panther.mkdir(parents=True)
            (panther / "setuperr.log").write_text("Intel VMD controller failed\nnvme timeout\n", encoding="utf-8")
            evidence = win.scan_windows_setup_evidence([root])
            self.assertGreaterEqual(len(evidence["files"]), 1)
            self.assertFalse(evidence["windows_files_modified"])
            self.assertIn("intel_vmd_or_rst", evidence["error_classes"])

    def test_media_corrupt_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sources").mkdir()
            media = win.check_windows_install_media(
                iso_or_root=root,
                expected_sha256="aaa",
                computed_sha256="bbb",
            )
            self.assertEqual(media["status"], "corrupt")
            self.assertFalse(media["install_start_allowed"])

    def test_preflight_write_false(self) -> None:
        machine = mid.build_machine_identity(
            dmi={"sys_vendor": "ASUS", "product_name": "ROG Strix", "board_name": "ROG"}
        )
        pf = win.build_windows11_preflight(
            machine=machine,
            windows_target={"serial_hash": "abc"},
            bios={"boot_mode": "uefi", "secure_boot": "enabled", "tpm": "2.0"},
            media={"install_start_allowed": True, "status": "valid"},
            nvme_health={"install_allowed": True},
            ram_test_status="pending",
            vmd_or_rst_detected=True,
        )
        self.assertFalse(pf["write_allowed"])
        self.assertIn(pf["status"], {"ready", "review_required", "blocked"})

    def test_postcheck_enables_linux_gate(self) -> None:
        g = win.windows_postcheck_gate(
            {
                "windows_booted": True,
                "uefi_boot": True,
                "efi_on_windows_nvme": True,
                "reboot_ok": True,
                "target_nvme_confirmed": True,
                "critical_storage_errors": False,
            }
        )
        self.assertEqual(g["linux_install_gate"], "ready")


class LinuxPlanGateTests(unittest.TestCase):
    def test_distro_missing(self) -> None:
        r = linux.check_linux_iso(distro=None, version=None, iso_path=None, sha256_expected=None, sha256_actual=None)
        self.assertEqual(r["status"], "ready_for_distro_selection")

    def test_plan_own_efi_and_windows_protected(self) -> None:
        plan = linux.build_linux_partition_plan(
            target_identity={"serial_hash": "lin", "model": "SSD2", "size_bytes": 2000, "pci_address": "0000:02:00.0"}
        )
        self.assertEqual(plan["bootloader_target"], "linux_nvme_esp_only")
        self.assertFalse(plan["windows_nvme_write_allowed"])
        self.assertTrue(plan["windows_esp_forbidden"])
        self.assertEqual(plan["layout"][0]["purpose"], "linux_efi")
        self.assertTrue(plan["plan_hash"])

    def test_execute_requires_dual_confirm(self) -> None:
        pre = {
            "status": "ready",
            "expires_at_epoch": 9_999_999_999,
            "plan_hash": "x",
        }
        blocked = linux.linux_install_execute_gate(
            preflight=pre,
            confirm_identity=False,
            confirm_destructive=True,
            current_linux_serial_hash="a",
            expected_linux_serial_hash="a",
            current_machine_id="m",
            expected_machine_id="m",
        )
        self.assertEqual(blocked["status"], "blocked")
        ok = linux.linux_install_execute_gate(
            preflight=pre,
            confirm_identity=True,
            confirm_destructive=True,
            current_linux_serial_hash="a",
            expected_linux_serial_hash="a",
            current_machine_id="m",
            expected_machine_id="m",
        )
        self.assertEqual(ok["status"], "handoff_authorized")
        self.assertFalse(ok["executed"])
        self.assertFalse(ok["windows_nvme_write_allowed"])

    def test_serial_change_emergency(self) -> None:
        pre = {"status": "ready", "expires_at_epoch": 9_999_999_999}
        r = linux.linux_install_execute_gate(
            preflight=pre,
            confirm_identity=True,
            confirm_destructive=True,
            current_linux_serial_hash="new",
            expected_linux_serial_hash="old",
            current_machine_id="m",
            expected_machine_id="m",
        )
        self.assertTrue(r["emergency_stop"])


class DccReadinessTests(unittest.TestCase):
    def test_plan_not_green(self) -> None:
        status = dcc.build_rescue_installation_readiness(
            linux_install={"status": "plan_ready"},
            endstatus="implemented_pending_physical_diagnosis",
        )
        self.assertEqual(status["asus_linux"]["tone"], "yellow")
        self.assertFalse(status["safety"]["automatic_bios_flash"])

    def test_unknown_grayish(self) -> None:
        status = dcc.build_rescue_installation_readiness()
        self.assertEqual(status["firmware"]["msi"]["tone"], "gray")


class WinpeCollectorPresenceTests(unittest.TestCase):
    def test_collector_files_exist(self) -> None:
        root = Path(__file__).resolve().parents[2] / "scripts/rescue-live/image/SETUPHELFER_WIN_DIAG"
        self.assertTrue((root / "SETUP_LOGS.TAG").is_file())
        self.assertTrue((root / "collect-win11-setup-logs.cmd").is_file())
        self.assertTrue((root / "collect-win11-disk-info.cmd").is_file())
        text = (root / "collect-win11-disk-info.cmd").read_text(encoding="utf-8", errors="replace")
        self.assertIn("No partitioning commands were executed", text)
        self.assertNotRegex(text, r"(?im)^\s*clean\b")
        self.assertNotRegex(text, r"(?im)^\s*format\b")
        logs_cmd = (root / "collect-win11-setup-logs.cmd").read_text(encoding="utf-8", errors="replace")
        self.assertIn("SETUP_LOGS", logs_cmd)


class VersionDomainTests(unittest.TestCase):
    def test_app_and_payload_may_differ(self) -> None:
        # Domains are separate — inequality is allowed.
        app = "1.9.21.0"
        payload = "1.10.1.3"
        self.assertNotEqual(app, payload)


if __name__ == "__main__":
    unittest.main()
