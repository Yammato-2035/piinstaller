"""PI-RS-ASUS-PHYSICAL-DIAG-003 capture/contract tests."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Sequence

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core import rescue_evidence_import_identity as ident  # noqa: E402
from core import rescue_hardware_discovery_capture as hdc  # noqa: E402
from core import rescue_machine_identity_profiles as mid  # noqa: E402
from core import rescue_nvme_install_target as nvme  # noqa: E402
from core import rescue_run_type_contract as rtype  # noqa: E402
from core import rescue_windows11_install_diag as win  # noqa: E402


def _fake_run_factory(responses: dict[tuple[str, ...], tuple[int, str, str]]):
    def _run(cmd: Sequence[str], timeout: float = 60.0) -> tuple[int, str, str]:
        key = tuple(cmd)
        if key in responses:
            return responses[key]
        # command -v checks
        if len(cmd) >= 3 and cmd[0] == "bash" and "command -v" in cmd[2]:
            name = cmd[2].split()[-1]
            if name in {
                "nvme",
                "smartctl",
                "lsblk",
                "blkid",
                "lspci",
                "udevadm",
                "journalctl",
                "dmesg",
                "dmidecode",
                "mount",
                "find",
                "sha256sum",
                "parted",
                "sgdisk",
                "fdisk",
            }:
                return 0, f"/usr/sbin/{name}\n", ""
            return 1, "", ""
        return 1, "", "unmocked"


    return _run


class RunTypeHardwareDiscoveryTests(unittest.TestCase):
    def test_no_bvr_run_control_required(self) -> None:
        r = rtype.evaluate_run_control(
            declared_run_type="hardware_discovery",
            artifact={
                "boot_id": "b",
                "machine_fingerprint_hash": "f",
                "payload_version": "1.10.2.0",
            },
        )
        self.assertEqual(r["status"], "discovery_complete")
        self.assertFalse(r["run_control_invalid_correct"])


class GabrielBindTests(unittest.TestCase):
    def test_g513qm_bind(self) -> None:
        ident_obj = mid.build_machine_identity(
            dmi={
                "sys_vendor": "ASUSTeK COMPUTER INC.",
                "product_name": "ROG Strix G513QM_G513QM",
                "board_name": "G513QM",
                "bios_version": "G513QM.331",
            }
        )
        bound = mid.bind_gabriel_operator_profile(
            ident_obj,
            operator_confirmed=True,
            exact_model_confirmed="ROG Strix G513QM",
            not_developer_host_ack=True,
            operator_phrase=mid.GABRIEL_OPERATOR_PHRASE,
        )
        self.assertTrue(bound["ok"])


class MsiImportRejectTests(unittest.TestCase):
    def test_msi_rejected(self) -> None:
        check = ident.session_compatible_with_expected(
            {
                "vendor": "Micro-Star International Co., Ltd.",
                "product_name": "GE63 Raider RGB 8RF",
                "board_name": "MS-16P5",
            },
            expected_manufacturer="ASUSTeK COMPUTER INC.",
            expected_board="G513QM",
        )
        self.assertFalse(check["ok"])


class NvmeIdentityTests(unittest.TestCase):
    def test_two_same_size_samsung_distinct(self) -> None:
        a = {
            "model": "Samsung SSD 970 EVO Plus 2TB",
            "serial": "S4EWNX0A1111111",
            "size_bytes": 2000398934016,
            "pci_address": "0000:04:00.0",
            "eui64": "002538b941a0b111",
            "nguid": None,
            "namespace_id": 1,
        }
        b = {
            "model": "Samsung SSD 970 EVO Plus 2TB",
            "serial": "S4EWNX0A2222222",
            "size_bytes": 2000398934016,
            "pci_address": "0000:05:00.0",
            "eui64": "002538b941a0b222",
            "nguid": None,
            "namespace_id": 1,
        }
        ha = hdc.compute_nvme_identity_hash(
            {
                "model": a["model"],
                "serial_hash": mid.hash_serial(a["serial"]),
                "eui64": a["eui64"],
                "nguid": "",
                "namespace_id": 1,
                "pci_address": a["pci_address"],
            }
        )
        hb = hdc.compute_nvme_identity_hash(
            {
                "model": b["model"],
                "serial_hash": mid.hash_serial(b["serial"]),
                "eui64": b["eui64"],
                "nguid": "",
                "namespace_id": 1,
                "pci_address": b["pci_address"],
            }
        )
        self.assertNotEqual(ha, hb)

    def test_device_rename_stable(self) -> None:
        entry = nvme.normalize_nvme_entry(
            {
                "model": "Samsung",
                "serial": "ABC12345",
                "size_bytes": 1000,
                "pci_address": "0000:04:00.0",
                "device_path": "/dev/nvme0n1",
                "eui64": "aabb",
            }
        )
        renamed = nvme.normalize_nvme_entry(
            {
                "model": "Samsung",
                "serial": "ABC12345",
                "size_bytes": 1000,
                "pci_address": "0000:04:00.0",
                "device_path": "/dev/nvme1n1",
                "eui64": "aabb",
            }
        )
        self.assertEqual(entry["identity_key"], renamed["identity_key"])
        self.assertEqual(entry["serial_masked"], "…2345")

    def test_eui_missing_nguid_present(self) -> None:
        h = hdc.compute_nvme_identity_hash(
            {
                "model": "M",
                "serial_hash": "abc",
                "eui64": "",
                "nguid": "11223344556677889900aabbccddeeff",
                "namespace_id": 1,
                "pci_address": "0000:04:00.0",
            }
        )
        self.assertTrue(h)

    def test_nguid_missing_eui_present(self) -> None:
        self.assertIsNone(hdc.normalize_hex_id("0000000000000000"))
        self.assertEqual(hdc.normalize_hex_id("002538b941a0b158"), "002538b941a0b158")

    def test_both_missing_reduces_confidence_path(self) -> None:
        # Via inventory path with mocked empty id-ns
        list_json = json.dumps(
            {
                "Devices": [
                    {
                        "DevicePath": "/dev/nvme0n1",
                        "ModelNumber": "Samsung",
                        "SerialNumber": "SERIALAAA1",
                        "Firmware": "1.0",
                        "PhysicalSize": 1000,
                    }
                ]
            }
        )
        responses = {
            ("nvme", "list", "-o", "json"): (0, list_json, ""),
            ("nvme", "list-subsys", "-o", "json"): (0, "{}", ""),
            ("nvme", "id-ctrl", "/dev/nvme0", "-o", "json"): (
                0,
                json.dumps({"mn": "Samsung", "sn": "SERIALAAA1", "fr": "1.0", "tnvmcap": 1000, "subnqn": "nqn"}),
                "",
            ),
            ("nvme", "id-ns", "/dev/nvme0n1", "-o", "json"): (0, json.dumps({"eui64": 0, "nguid": 0}), ""),
            ("bash", "-lc", "readlink -f /sys/class/block/nvme0n1/device"): (
                0,
                "/sys/devices/pci0000:00/0000:00:01.1/0000:04:00.0/nvme/nvme0\n",
                "",
            ),
        }
        inv = hdc.collect_nvme_inventory(run=_fake_run_factory(responses))
        self.assertEqual(inv["devices_redacted"][0]["identity_confidence"], "medium")
        self.assertIn("eui64", inv["devices_redacted"][0]["missing_identity_fields"])
        self.assertIn("nguid", inv["devices_redacted"][0]["missing_identity_fields"])


class SmartClassificationTests(unittest.TestCase):
    def test_healthy(self) -> None:
        self.assertEqual(hdc.classify_smart_health({"critical_warning": 0, "media_errors": 0}), "HEALTHY")

    def test_warning(self) -> None:
        self.assertEqual(
            hdc.classify_smart_health({"critical_warning": 0, "media_errors": 0, "unsafe_shutdowns": 99}),
            "WARNING",
        )

    def test_critical(self) -> None:
        self.assertEqual(hdc.classify_smart_health({"critical_warning": 1, "media_errors": 0}), "CRITICAL")
        self.assertEqual(hdc.classify_smart_health({"critical_warning": 0, "media_errors": 3}), "CRITICAL")

    def test_unknown(self) -> None:
        self.assertEqual(hdc.classify_smart_health({}), "UNKNOWN")


class ErrorLogAndKernelTests(unittest.TestCase):
    def test_empty_error_log_ok(self) -> None:
        health = hdc.collect_nvme_health(
            inventory={
                "devices_redacted": [
                    {
                        "controller": "/dev/nvme0",
                        "device_path": "/dev/nvme0n1",
                        "nvme_identity_hash": "h",
                        "firmware_revision": "1",
                    }
                ]
            },
            run=_fake_run_factory(
                {
                    ("nvme", "smart-log", "/dev/nvme0", "-o", "json"): (
                        0,
                        json.dumps({"critical_warning": 0, "media_errors": 0, "num_err_log_entries": 0}),
                        "",
                    ),
                    ("nvme", "error-log", "/dev/nvme0", "--log-entries=64", "-o", "json"): (
                        0,
                        json.dumps({"errors": []}),
                        "",
                    ),
                    ("smartctl", "-x", "-j", "/dev/nvme0n1"): (0, "{}", ""),
                }
            ),
        )
        self.assertEqual(health["devices"][0]["error_log_entries"], 0)
        self.assertEqual(health["devices"][0]["health_label"], "HEALTHY")


class NtfsMountTests(unittest.TestCase):
    def test_read_only_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mp = Path(tmp) / "m"
            calls: list[tuple[str, ...]] = []

            def run(cmd: Sequence[str], timeout: float = 60.0) -> tuple[int, str, str]:
                calls.append(tuple(cmd))
                if cmd[0] == "mount":
                    return 0, "", ""
                if cmd[0] == "findmnt":
                    return 0, "ro,norecover\n", ""
                return 1, "", ""

            r = hdc.mount_ntfs_read_only("/dev/nvme0n1p3", mp, run=run)
            self.assertEqual(r["status"], "mounted_ro")
            self.assertTrue(r["read_only_confirmed"])

    def test_hibernated_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mp = Path(tmp) / "m"

            def run(cmd: Sequence[str], timeout: float = 60.0) -> tuple[int, str, str]:
                if cmd[0] == "mount":
                    return 32, "", "Windows is hibernated, refused to mount."
                return 1, "", ""

            r = hdc.mount_ntfs_read_only("/dev/nvme0n1p3", mp, run=run)
            self.assertEqual(r["status"], "ntfs_read_only_mount_blocked")


class WindowsLogTests(unittest.TestCase):
    def test_panther_found(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            panther = root / "Windows" / "Panther"
            panther.mkdir(parents=True)
            (panther / "setuperr.log").write_text("Error 0x8007045d storage driver", encoding="utf-8")
            scan = win.scan_windows_setup_evidence([root])
            self.assertEqual(scan["status"], "ok")
            self.assertTrue(scan["files"])

    def test_no_logs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            scan = win.scan_windows_setup_evidence([Path(tmp)])
            self.assertEqual(scan["status"], "insufficient_evidence")

    def test_redaction(self) -> None:
        text = hdc.redact_text("user john@example.com key AAAAA-BBBBB-CCCCC-DDDDD-EEEEE serial SUPERSECRET99", ["SUPERSECRET99"])
        self.assertNotIn("john@example.com", text)
        self.assertNotIn("SUPERSECRET99", text)
        self.assertIn("[redacted-email]", text)


class CauseAndRolesTests(unittest.TestCase):
    def test_cause_matrix_insufficient_without_logs(self) -> None:
        m = hdc.build_cause_matrix(
            nvme_health={"devices": [{"health_label": "HEALTHY"}]},
            kernel={"critical_io_or_mce": False},
            windows_logs={"panther_found": False, "rollback_found": False, "files": []},
        )
        self.assertEqual(m["confidence"], "low")
        self.assertEqual(m["likely_cause"], "unknown")

    def test_endstatus_retest_when_healthy_no_logs(self) -> None:
        end = hdc.decide_endstatus(
            binding_ok=True,
            identity_conflict=False,
            nvme_health={"devices": [{"health_label": "HEALTHY"}, {"health_label": "HEALTHY"}]},
            windows_logs={"panther_found": False, "files": []},
            capture_complete=True,
        )
        self.assertEqual(end, "ready_for_controlled_windows_retest_with_log_collection")

    def test_role_binding_no_write(self) -> None:
        manifest = nvme.build_asus_install_targets_manifest(
            windows={"serial": "AAAA1111", "model": "S", "size_bytes": 1, "pci_address": "0000:04:00.0"},
            linux={"serial": "BBBB2222", "model": "S", "size_bytes": 1, "pci_address": "0000:05:00.0"},
        )
        self.assertFalse(manifest["write_allowed_windows"])
        self.assertFalse(manifest["write_allowed_linux"])
        self.assertTrue(manifest["targets_distinct"])


class StatusFileContractTests(unittest.TestCase):
    def test_status_schema(self) -> None:
        st = hdc.build_run_status(
            profile_id="asus_rog_gabriel",
            machine_fingerprint_hash="abc",
            boot_id="boot",
            run_id="run",
            payload_version="1.10.2.0",
        )
        self.assertEqual(st["run_type"], "hardware_discovery")
        self.assertFalse(st["write_operations_allowed"])
        self.assertFalse(st["bvr_run_control_required"])
        self.assertIn("nvme_inventory", st["captures"])


if __name__ == "__main__":
    unittest.main()
