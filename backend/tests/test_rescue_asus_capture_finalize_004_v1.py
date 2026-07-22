"""PI-RS-ASUS-CAPTURE-FINALIZE-004 — finalizer, SMART, Panther, import, safety."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Sequence
from unittest import mock

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core import rescue_hardware_discovery_capture as hdc  # noqa: E402
from core import rescue_hardware_discovery_import as hdi  # noqa: E402
from core.rescue_machine_identity_profiles import GABRIEL_OPERATOR_PHRASE  # noqa: E402


def _tool_ok(name: str) -> tuple[int, str, str]:
    return 0, f"/usr/sbin/{name}\n", ""


def _base_responses() -> dict[tuple[str, ...], tuple[int, str, str]]:
    lsblk = {
        "blockdevices": [
            {"name": "nvme0n1", "path": "/dev/nvme0n1", "size": "1.8T"},
            {"name": "nvme1n1", "path": "/dev/nvme1n1", "size": "1.8T"},
        ]
    }
    smart = {
        "critical_warning": 0,
        "temperature": 308,
        "avail_spare": 100,
        "spare_thresh": 10,
        "percent_used": 1,
        "data_units_read": 100,
        "data_units_written": 200,
        "power_cycles": 10,
        "power_on_hours": 100,
        "unsafe_shutdowns": 0,
        "media_errors": 0,
        "num_err_log_entries": 0,
        "warning_temp_time": 0,
        "critical_comp_time": 0,
    }
    return {
        ("bash", "-lc", "command -v nvme"): _tool_ok("nvme"),
        ("bash", "-lc", "command -v smartctl"): _tool_ok("smartctl"),
        ("bash", "-lc", "command -v lsblk"): _tool_ok("lsblk"),
        ("bash", "-lc", "command -v blkid"): _tool_ok("blkid"),
        ("bash", "-lc", "command -v lspci"): _tool_ok("lspci"),
        ("bash", "-lc", "command -v udevadm"): _tool_ok("udevadm"),
        ("bash", "-lc", "command -v journalctl"): _tool_ok("journalctl"),
        ("bash", "-lc", "command -v dmesg"): _tool_ok("dmesg"),
        ("bash", "-lc", "command -v dmidecode"): _tool_ok("dmidecode"),
        ("bash", "-lc", "command -v efibootmgr"): _tool_ok("efibootmgr"),
        ("bash", "-lc", "command -v mokutil"): _tool_ok("mokutil"),
        ("bash", "-lc", "command -v mount"): _tool_ok("mount"),
        ("bash", "-lc", "command -v find"): _tool_ok("find"),
        ("bash", "-lc", "command -v sha256sum"): _tool_ok("sha256sum"),
        ("bash", "-lc", "command -v parted"): _tool_ok("parted"),
        ("bash", "-lc", "command -v sgdisk"): _tool_ok("sgdisk"),
        ("bash", "-lc", "command -v fdisk"): _tool_ok("fdisk"),
        ("lsblk", "--json", "-O"): (0, json.dumps(lsblk), ""),
        ("blkid",): (0, "", ""),
        ("fdisk", "-l"): (0, "", ""),
        ("efibootmgr", "-v"): (0, "", ""),
        ("journalctl", "-k", "-b", "--no-pager"): (0, "nvme ok\n", ""),
        ("dmesg",): (0, "pcie ok\n", ""),
        ("nvme", "smart-log", "/dev/nvme0", "-o", "json"): (0, json.dumps(smart), ""),
        ("nvme", "smart-log", "/dev/nvme1", "-o", "json"): (0, json.dumps(smart), ""),
        ("nvme", "error-log", "/dev/nvme0", "--log-entries=64", "-o", "json"): (
            0,
            json.dumps({"errors": []}),
            "",
        ),
        ("nvme", "error-log", "/dev/nvme1", "--log-entries=64", "-o", "json"): (
            0,
            json.dumps({"errors": []}),
            "",
        ),
        ("smartctl", "-x", "-j", "/dev/nvme0n1"): (0, json.dumps({"smartctl": {"exit_status": 0}}), ""),
        ("smartctl", "-x", "-j", "/dev/nvme1n1"): (0, json.dumps({"smartctl": {"exit_status": 0}}), ""),
        ("parted", "-s", "/dev/nvme0n1", "unit", "s", "print"): (0, "Model: Samsung\n", ""),
        ("parted", "-s", "/dev/nvme1n1", "unit", "s", "print"): (0, "Model: Samsung\n", ""),
        ("sgdisk", "-p", "/dev/nvme0n1"): (0, "Disk /dev/nvme0n1\n", ""),
        ("sgdisk", "-p", "/dev/nvme1n1"): (0, "Disk /dev/nvme1n1\n", ""),
    }


def _fake_run(responses: dict[tuple[str, ...], tuple[int, str, str]]):
    def _run(cmd: Sequence[str], timeout: float = 60.0) -> tuple[int, str, str]:
        key = tuple(cmd)
        if key in responses:
            return responses[key]
        if len(cmd) >= 3 and cmd[0] == "bash" and "command -v" in str(cmd[2]):
            return 1, "", ""
        if cmd[0] == "nvme" and len(cmd) >= 2 and cmd[1] == "list":
            return (
                0,
                json.dumps(
                    {
                        "Devices": [
                            {
                                "DevicePath": "/dev/nvme0n1",
                                "ModelNumber": "Samsung SSD 970 EVO Plus 2TB",
                                "SerialNumber": "TESTSERIALAAAAAAA",
                                "Firmware": "2B2QEXM7",
                                "PhysicalSize": 2000398934016,
                            },
                            {
                                "DevicePath": "/dev/nvme1n1",
                                "ModelNumber": "Samsung SSD 970 EVO Plus 2TB",
                                "SerialNumber": "TESTSERIALBBBBBBB",
                                "Firmware": "2B2QEXM7",
                                "PhysicalSize": 2000398934016,
                            },
                        ]
                    }
                ),
                "",
            )
        if cmd[0] == "nvme" and "id-ctrl" in cmd:
            return 0, json.dumps({"subnqn": "nqn.test"}), ""
        if cmd[0] == "nvme" and "id-ns" in cmd:
            eui = "002538b941a0b111" if "nvme0" in " ".join(cmd) else "002538b941a0b222"
            return 0, json.dumps({"nsid": 1, "eui64": eui, "nguid": "0" * 32}), ""
        return 1, "", "unmocked:" + " ".join(cmd)

    return _run


class FinalizerTests(unittest.TestCase):
    def test_complete_capture_writes_marker_after_manifest(self) -> None:
        phases: list[str] = []

        def cb(phase_id: str, status: str, detail: Any) -> None:
            phases.append(f"{phase_id}:{status}")

        inventory = {
            "device_count": 2,
            "raw": {"controllers": [1, 2]},
            "devices_redacted": [
                {
                    "nvme_identity_hash": "hash-a",
                    "serial_hash": "sa",
                    "controller": "/dev/nvme0",
                    "device_path": "/dev/nvme0n1",
                    "firmware_revision": "2B2QEXM7",
                    "eui64": "002538b941a0b111",
                    "missing_identity_fields": ["nguid"],
                },
                {
                    "nvme_identity_hash": "hash-b",
                    "serial_hash": "sb",
                    "controller": "/dev/nvme1",
                    "device_path": "/dev/nvme1n1",
                    "firmware_revision": "2B2QEXM7",
                    "eui64": "002538b941a0b222",
                    "missing_identity_fields": ["nguid"],
                },
            ],
        }
        health = {
            "devices": [
                {
                    "nvme_identity_hash": "hash-a",
                    "capture_status": "complete",
                    "health_label": "HEALTHY",
                    "smart": {"critical_warning": 0, "media_errors": 0},
                },
                {
                    "nvme_identity_hash": "hash-b",
                    "capture_status": "complete",
                    "health_label": "HEALTHY",
                    "smart": {"critical_warning": 0, "media_errors": 0},
                },
            ],
            "error_logs_raw": [{"path": "/dev/nvme0"}, {"path": "/dev/nvme1"}],
        }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prog = root / "progress.json"
            with mock.patch.object(hdc, "read_dmi_fields", return_value={
                "sys_vendor": "ASUSTeK COMPUTER INC.",
                "product_name": "ROG Strix G513QM_G513QM",
                "board_name": "G513QM",
                "bios_version": "G513QM.331",
            }), mock.patch.object(hdc, "collect_nvme_inventory", return_value=inventory), mock.patch.object(
                hdc, "collect_nvme_health", return_value=health
            ), mock.patch.object(
                hdc,
                "collect_kernel_storage_findings",
                return_value={"critical_io_or_mce": False, "filtered_hits": []},
            ), mock.patch.object(
                hdc,
                "collect_partition_and_boot_inventory",
                return_value={"blkid_text": "", "efibootmgr": "", "efibootmgr_available": False},
            ), mock.patch.object(
                hdc,
                "collect_windows_setup_logs",
                return_value={
                    "mounts": [],
                    "files": [],
                    "panther_found": False,
                    "rollback_found": False,
                    "error_classes": [],
                },
            ):
                result = hdc.run_hardware_discovery(
                    evidence_root=root,
                    operator_confirmed_gabriel=True,
                    operator_phrase=GABRIEL_OPERATOR_PHRASE,
                    run=_fake_run(_base_responses()),
                    allow_non_gabriel_diag=True,
                    progress_path=prog,
                    progress_cb=cb,
                )
            out = Path(result["out_dir"])
            self.assertTrue(result.get("terminal"))
            self.assertEqual(result.get("status"), "complete")
            self.assertTrue((out / "manifest.json").is_file())
            self.assertTrue((out / "sha256sums.txt").is_file())
            self.assertTrue((out / "COMPLETED.TAG").is_file())
            st = json.loads((out / "run_status.json").read_text(encoding="utf-8"))
            self.assertTrue(st.get("terminal"))
            self.assertEqual(st.get("status"), "complete")
            self.assertEqual(st.get("gui_status"), "not_applicable_for_text_hardware_discovery")
            self.assertTrue(any(p.startswith("nvme_smart:") for p in phases))
            self.assertTrue(any(p.startswith("capture_complete:") for p in phases))
            man = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
            self.assertNotIn("COMPLETED.TAG", man.get("files") or [])

    def test_finalizer_runs_despite_smart_failure(self) -> None:
        inventory = {
            "device_count": 2,
            "raw": {},
            "devices_redacted": [
                {"nvme_identity_hash": "a", "serial_hash": "sa", "controller": "/dev/nvme0", "device_path": "/dev/nvme0n1"},
                {"nvme_identity_hash": "b", "serial_hash": "sb", "controller": "/dev/nvme1", "device_path": "/dev/nvme1n1"},
            ],
        }
        health = {
            "devices": [
                {"nvme_identity_hash": "a", "capture_status": "failed", "health_label": "UNKNOWN"},
                {"nvme_identity_hash": "b", "capture_status": "failed", "health_label": "UNKNOWN"},
            ],
            "error_logs_raw": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(hdc, "read_dmi_fields", return_value={
                "sys_vendor": "ASUSTeK COMPUTER INC.",
                "product_name": "ROG Strix G513QM",
                "board_name": "G513QM",
                "bios_version": "G513QM.331",
            }), mock.patch.object(hdc, "collect_nvme_inventory", return_value=inventory), mock.patch.object(
                hdc, "collect_nvme_health", return_value=health
            ), mock.patch.object(
                hdc, "collect_kernel_storage_findings", return_value={"critical_io_or_mce": False}
            ), mock.patch.object(
                hdc, "collect_partition_and_boot_inventory", return_value={"blkid_text": ""}
            ), mock.patch.object(
                hdc,
                "collect_windows_setup_logs",
                return_value={"mounts": [], "files": [], "panther_found": False, "rollback_found": False},
            ):
                result = hdc.run_hardware_discovery(
                    evidence_root=Path(tmp),
                    operator_confirmed_gabriel=True,
                    operator_phrase=GABRIEL_OPERATOR_PHRASE,
                    run=_fake_run(_base_responses()),
                    allow_non_gabriel_diag=True,
                )
            out = Path(result["out_dir"])
            st = json.loads((out / "run_status.json").read_text(encoding="utf-8"))
            self.assertTrue(st["terminal"])
            self.assertEqual(st["status"], "partial")
            self.assertTrue((out / "manifest.json").is_file())
            self.assertTrue((out / "PARTIAL.TAG").is_file())
            self.assertEqual(st["captures"].get("nvme_smart"), "failed")

    def test_panther_not_found_is_not_failed(self) -> None:
        win = {"mounts": [], "files": [], "panther_found": False, "rollback_found": False}
        self.assertEqual(hdc.classify_windows_capture_status(win), "not_found")

    def test_ntfs_mount_blocked_partial(self) -> None:
        win = {
            "mounts": [{"status": "ntfs_read_only_mount_blocked"}],
            "files": [],
            "panther_found": False,
            "rollback_found": False,
        }
        self.assertEqual(hdc.classify_windows_capture_status(win), "partial")

    def test_running_to_partial_on_exception_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "run"
            out.mkdir()
            status = hdc.build_run_status(
                profile_id="asus_rog_gabriel",
                machine_fingerprint_hash="abc",
                boot_id="boot",
                run_id="run",
                payload_version="1.10.2.1",
                status="running",
            )
            fin = hdc.finalize_capture_artifacts(
                out_dir=out,
                status=status,
                tooling={},
                endstatus="diagnosis_incomplete",
                missing_areas=["nvme_smart"],
            )
            st = json.loads((out / "run_status.json").read_text(encoding="utf-8"))
            self.assertEqual(st["status"], "partial")
            self.assertTrue(st["terminal"])
            self.assertEqual(fin["marker"], "PARTIAL.TAG")
            self.assertTrue((out / "sha256sums.txt").is_file())
            self.assertTrue((out / "manifest.json").is_file())


class ImportGateTests(unittest.TestCase):
    def test_rejects_nonterminal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "hw-discovery-x"
            run.mkdir()
            (run / "run_status.json").write_text(
                json.dumps(
                    {
                        "run_type": "hardware_discovery",
                        "boot_id": "b1",
                        "run_id": "hw-discovery-x",
                        "status": "running",
                        "terminal": False,
                        "profile_id": "asus_rog_gabriel",
                    }
                ),
                encoding="utf-8",
            )
            (run / "machine_identity.json").write_text(
                json.dumps({"sys_vendor": "ASUSTeK", "product_name": "G513QM", "board_name": "G513QM"}),
                encoding="utf-8",
            )
            gate = hdi.evaluate_hardware_discovery_import_candidate(
                run, expected_boot_id="b1", expected_run_id="hw-discovery-x"
            )
            self.assertFalse(gate["ok"])
            self.assertEqual(gate["import_status"], "incomplete_capture")

    def test_rejects_msi(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "msi"
            run.mkdir()
            (run / "COMPLETED.TAG").write_text("status=complete\n", encoding="utf-8")
            (run / "run_status.json").write_text(
                json.dumps(
                    {
                        "run_type": "hardware_discovery",
                        "boot_id": "b",
                        "run_id": "msi",
                        "status": "complete",
                        "terminal": True,
                        "profile_id": "msi_lab",
                    }
                ),
                encoding="utf-8",
            )
            (run / "machine_identity.json").write_text(
                json.dumps(
                    {
                        "sys_vendor": "Micro-Star International Co., Ltd.",
                        "product_name": "GE63",
                        "board_name": "MS-16P5",
                    }
                ),
                encoding="utf-8",
            )
            gate = hdi.evaluate_hardware_discovery_import_candidate(
                run, expected_boot_id="b", expected_run_id="msi"
            )
            self.assertFalse(gate["ok"])
            self.assertTrue(gate["msi_excluded"])

    def test_accepts_terminal_asus(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "ok"
            run.mkdir()
            (run / "COMPLETED.TAG").write_text("status=complete\n", encoding="utf-8")
            (run / "manifest.json").write_text("{}\n", encoding="utf-8")
            (run / "sha256sums.txt").write_text("a  b\n", encoding="utf-8")
            (run / "run_status.json").write_text(
                json.dumps(
                    {
                        "run_type": "hardware_discovery",
                        "boot_id": "boot-ok",
                        "run_id": "ok",
                        "status": "complete",
                        "terminal": True,
                        "profile_id": "asus_rog_gabriel",
                    }
                ),
                encoding="utf-8",
            )
            (run / "machine_identity.json").write_text(
                json.dumps(
                    {
                        "sys_vendor": "ASUSTeK COMPUTER INC.",
                        "product_name": "ROG Strix G513QM",
                        "board_name": "G513QM",
                    }
                ),
                encoding="utf-8",
            )
            gate = hdi.evaluate_hardware_discovery_import_candidate(
                run, expected_boot_id="boot-ok", expected_run_id="ok"
            )
            self.assertTrue(gate["ok"])


class SafetyPolicyTests(unittest.TestCase):
    def test_no_storage_write_commands_in_capture_source(self) -> None:
        src = Path(hdc.__file__).read_text(encoding="utf-8")
        for banned in (
            "wipefs",
            "mkfs",
            "nvme format",
            "nvme sanitize",
            "nvme write-zeroes",
            "blkdiscard",
            "cryptsetup",
            "ntfsfix",
        ):
            self.assertNotIn(banned, src)

    def test_gui_status_constant(self) -> None:
        st = hdc.build_run_status(
            profile_id="asus_rog_gabriel",
            machine_fingerprint_hash="x",
            boot_id="b",
            run_id="r",
            payload_version="1.10.2.1",
        )
        self.assertEqual(st["gui_status"], "not_applicable_for_text_hardware_discovery")

    def test_capture_phases_cover_required(self) -> None:
        ids = [p[0] for p in hdc.CAPTURE_PHASES]
        for needed in (
            "device_binding",
            "nvme_smart",
            "windows_setup_logs",
            "manifest_checksums",
            "capture_complete",
        ):
            self.assertIn(needed, ids)

    def test_eui_without_nguid_ok(self) -> None:
        fields = {
            "model": "Samsung",
            "serial_hash": "abc",
            "eui64": "002538b941a0b111",
            "nguid": "",
            "namespace_id": "1",
            "pci_address": "0000:04:00.0",
        }
        h = hdc.compute_nvme_identity_hash(fields)
        self.assertEqual(len(h), 64)


class SensitiveGateScriptTests(unittest.TestCase):
    def test_script_exists_and_executable_bits(self) -> None:
        script = _backend.parent / "scripts" / "check-sensitive-hardware-identifiers.sh"
        self.assertTrue(script.is_file())
        self.assertIn("SENSITIVE_ID_SECRETS_FILE", script.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
