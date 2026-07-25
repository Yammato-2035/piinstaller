"""PI-RS-INSTALL-ASSISTANT-001 — disk role bind, diagnosis, ISO, dry-run, BIOS, handoff."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core import rescue_install_bios_session as bios_sess  # noqa: E402
from core import rescue_install_diagnosis as diag  # noqa: E402
from core import rescue_install_distro_profiles as distro  # noqa: E402
from core import rescue_linux_second_nvme as linux  # noqa: E402
from core import rescue_nvme_install_target as nvme  # noqa: E402


def _nvme(
    serial: str,
    path: str,
    model: str = "Samsung SSD",
    size: int = 1024**3,
    pci: str | None = None,
) -> dict:
    return {
        "device_path": path,
        "model": model,
        "serial": serial,
        "size_bytes": size,
        "pci_address": pci or "0000:01:00.0",
        "smart_status": "healthy",
    }


class DiskRoleBindTests(unittest.TestCase):
    def test_same_fingerprint_survives_device_rename(self) -> None:
        a = nvme.normalize_nvme_entry(_nvme("WINSERIAL01", "/dev/nvme0n1", pci="0000:01:00.0"))
        b = nvme.normalize_nvme_entry(_nvme("WINSERIAL01", "/dev/nvme1n1", pci="0000:01:00.0"))
        self.assertEqual(a["serial_hash"], b["serial_hash"])
        self.assertEqual(a["identity_key"], b["identity_key"])
        inv = [
            _nvme("WINSERIAL01", "/dev/nvme1n1", pci="0000:01:00.0"),
            _nvme("LINUXSERIAL02", "/dev/nvme0n1", pci="0000:02:00.0"),
        ]
        targets = {
            "windows_target": {"serial_hash": a["serial_hash"]},
            "linux_target": {
                "serial_hash": nvme.hash_serial("LINUXSERIAL02"),
            },
        }
        resolved = nvme.resolve_role_after_device_rename(inv, targets)
        self.assertTrue(resolved["ok"])
        self.assertEqual(resolved["windows"]["entry"]["device_path"], "/dev/nvme1n1")
        self.assertEqual(resolved["linux"]["entry"]["device_path"], "/dev/nvme0n1")

    def test_wrong_hash_blocks_bind(self) -> None:
        inv = [_nvme("REAL", "/dev/nvme0n1")]
        bad = nvme.bind_role_by_identity(
            inv, serial_hash=nvme.hash_serial("WRONG"), role="linux_target"
        )
        self.assertFalse(bad["ok"])
        self.assertEqual(bad["error"], "ambiguous_or_missing_nvme_identity")

    def test_rescue_stick_excluded_from_linux_target(self) -> None:
        stick = {
            "device_path": "/dev/sda",
            "model": "Ultra Line",
            "serial": "STICKSERIAL",
            "size_bytes": 64 * 1024**3,
            "transport": "usb",
            "partitions": [{"label": "SETUPHELFER"}],
        }
        inv = [stick, _nvme("LINUXOK", "/dev/nvme0n1")]
        stick_hash = nvme.hash_serial("STICKSERIAL")
        blocked = nvme.bind_role_by_identity(inv, serial_hash=stick_hash, role="linux_target")
        self.assertFalse(blocked["ok"])
        ok = nvme.bind_role_by_identity(
            inv, serial_hash=nvme.hash_serial("LINUXOK"), role="linux_target"
        )
        self.assertTrue(ok["ok"])
        self.assertEqual(ok["entry"]["intended_role"], "linux_target")
        self.assertFalse(ok["entry"]["write_allowed"])


class InstallDiagnosisTests(unittest.TestCase):
    def test_issue_codes_and_ampel(self) -> None:
        d = diag.build_install_diagnosis(
            aer_flood=True,
            bios_compare={"status": "update_available"},
            disk_roles={"targets_distinct": False},
            iso_status={"status": "corrupt", "sha256_ok": False},
            locale="de",
        )
        self.assertEqual(d["ampel"], "red")
        self.assertIn("pcie_aer_flood_blocks_installer", d["issue_codes"])
        self.assertIn("bios_outdated_likely", d["issue_codes"])
        self.assertIn("disk_role_ambiguous", d["issue_codes"])
        self.assertIn("installer_media_corrupt", d["issue_codes"])
        self.assertFalse(d["bios_flash_allowed"])
        red = diag.redact_install_diagnosis_for_upload(d)
        self.assertFalse(red["pii_allowed"])
        self.assertEqual(red["issue_codes"], d["issue_codes"])


class DistroIsoTests(unittest.TestCase):
    def test_profiles_stubs_and_mint_p0(self) -> None:
        profiles = distro.list_distro_profiles()
        ids = {p["id"] for p in profiles["profiles"]}
        self.assertEqual(profiles["p0_distro"], "linux_mint")
        self.assertIn("linux_mint", ids)
        self.assertIn("ubuntu_server_lts", ids)
        self.assertIn("debian", ids)
        self.assertEqual(profiles["linux_install_capability"], "preview")
        self.assertFalse(profiles["auto_download_allowed"])

    def test_wrong_hash_fails_missing_does_not_crash(self) -> None:
        missing = distro.resolve_iso_status(profile_id="linux_mint")
        self.assertEqual(missing["status"], "missing")
        bad = linux.check_linux_iso(
            distro="linux_mint",
            version="22",
            iso_path="/tmp/fake.iso",
            sha256_expected="aaaa",
            sha256_actual="bbbb",
        )
        self.assertEqual(bad["status"], "corrupt")
        self.assertFalse(bad["install_allowed"])
        policy = distro.download_policy_gate(operator_started=False, profile_id="linux_mint")
        self.assertFalse(policy["allowed"])


class PartitionDryRunTests(unittest.TestCase):
    def test_plan_hash_stable_and_windows_role_blocked(self) -> None:
        target = nvme.normalize_nvme_entry(_nvme("LINUX", "/dev/nvme1n1"))
        target["intended_role"] = "linux_target"
        p1 = linux.build_linux_partition_plan(target_identity=target)
        p2 = linux.build_linux_partition_plan(target_identity=target)
        self.assertEqual(p1["plan_hash"], p2["plan_hash"])
        self.assertFalse(p1["write_allowed"])
        self.assertFalse(p1["windows_nvme_write_allowed"])
        win = dict(target)
        win["intended_role"] = "windows_system"
        blocked = linux.build_linux_partition_plan(target_identity=win)
        self.assertEqual(blocked["status"], "blocked")
        self.assertEqual(blocked["error"], "windows_role_forbidden_as_mint_target")


class BiosSessionTests(unittest.TestCase):
    def test_read_only_session_no_flash(self) -> None:
        machine = {
            "expected_profile": "asus_rog_gabriel",
            "confidence": "high",
            "bios_version": "G513QM.331",
            "board_name": "G513QM",
            "product_name": "ROG Strix G513QM_G513QM",
            "manufacturer": "ASUS",
        }
        session = bios_sess.build_bios_session(machine=machine, locale="de")
        self.assertFalse(session["automatic_flash_allowed"])
        self.assertFalse(session["boot_next_allowed"])
        self.assertFalse(session["blocks_mint_dry_run"])
        self.assertTrue(session["checklist"])
        cmp = session["compare"]
        self.assertFalse(cmp["automatic_flash_allowed"])
        self.assertEqual(cmp.get("latest_official_version"), "G513QM.335")
        evidence = bios_sess.export_bios_session_evidence(session)
        self.assertEqual(evidence["mode"], "read_only")


class MintHandoffTests(unittest.TestCase):
    def test_execute_handoff_requires_gates_never_wipes(self) -> None:
        win = {"serial_hash": nvme.hash_serial("WIN")}
        lin = {"serial_hash": nvme.hash_serial("LIN")}
        iso = linux.check_linux_iso(
            distro="linux_mint",
            version="22",
            iso_path="/cache/mint.iso",
            sha256_expected="abc",
            sha256_actual="abc",
        )
        plan = linux.build_linux_partition_plan(
            target_identity={**lin, "model": "X", "intended_role": "linux_target"}
        )
        pre = linux.linux_install_preflight(
            machine={"machine_id": "m1", "gabriel_bound": True},
            windows_postcheck_ok=True,
            windows_target=win,
            linux_target=lin,
            iso=iso,
            plan=plan,
            nvme_health_linux={"install_allowed": True},
            backup_ack=True,
        )
        self.assertEqual(pre["status"], "ready")
        self.assertFalse(pre["execute"])
        blocked = linux.linux_install_execute_gate(
            preflight=pre,
            confirm_identity=True,
            confirm_destructive=True,
            current_linux_serial_hash=lin["serial_hash"],
            expected_linux_serial_hash=lin["serial_hash"],
            current_machine_id="m1",
            expected_machine_id="m1",
            operator_phrase="wrong",
        )
        self.assertEqual(blocked["status"], "blocked")
        self.assertFalse(blocked["executed"])
        ok = linux.linux_install_execute_gate(
            preflight=pre,
            confirm_identity=True,
            confirm_destructive=True,
            current_linux_serial_hash=lin["serial_hash"],
            expected_linux_serial_hash=lin["serial_hash"],
            current_machine_id="m1",
            expected_machine_id="m1",
            operator_phrase="INSTALL LINUX TARGET",
        )
        self.assertEqual(ok["status"], "handoff_authorized")
        self.assertFalse(ok["executed"])
        self.assertEqual(ok["mode"], "handoff")
        verify = linux.post_install_verify(
            linux_target=lin,
            windows_target=win,
            linux_bootable=True,
            windows_unchanged=True,
        )
        self.assertEqual(verify["status"], "verified")


class ApiRouteSmokeTests(unittest.TestCase):
    def test_router_mounts(self) -> None:
        import asyncio

        from api.routes import rescue as rescue_routes
        from api.routes.rescue_install_assistant import post_linux_install_execute, router

        paths = {getattr(r, "path", None) for r in router.routes}
        self.assertIn("/install-assistant/status", paths)
        self.assertIn("/install-assistant/linux/install-execute", paths)
        self.assertIsNotNone(rescue_routes.rescue_install_assistant_router)
        result = asyncio.run(
            post_linux_install_execute(
                {
                    "preflight": {"status": "ready"},
                    "confirm_identity": True,
                    "confirm_destructive": True,
                    "current_linux_serial_hash": "a",
                    "expected_linux_serial_hash": "a",
                    "current_machine_id": "m",
                    "expected_machine_id": "m",
                    "operator_phrase": "INSTALL LINUX TARGET",
                }
            )
        )
        self.assertFalse(result["executed"])
        self.assertEqual(result["status"], "handoff_authorized")


if __name__ == "__main__":
    unittest.main()
