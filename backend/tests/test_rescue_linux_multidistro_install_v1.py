"""Tests for multi-distro Linux install contracts and ASUS orchestration."""

from __future__ import annotations

import unittest

from core.rescue_asus_mint_orchestration_v1 import build_asus_mint_orchestration_plan
from core.rescue_linux_distro_profiles_v1 import distro_install_allowed, list_distro_profiles
from core.rescue_linux_install_diagnosis_v1 import classify_install_diagnosis
from core.rescue_linux_install_gate_v1 import evaluate_install_gate
from core.rescue_linux_second_nvme import check_linux_iso, linux_install_execute_gate
from core.rescue_nvme_install_target import hash_serial, normalize_nvme_entry


class LinuxDistroProfilesV1Tests(unittest.TestCase):
    def test_four_profiles(self) -> None:
        profiles = list_distro_profiles(include_planned=True)
        ids = {p["id"] for p in profiles}
        self.assertEqual(ids, {"linux_mint", "ubuntu_server_lts", "ubuntu_server", "debian"})

    def test_only_mint_supported(self) -> None:
        self.assertTrue(distro_install_allowed("linux_mint"))
        self.assertFalse(distro_install_allowed("ubuntu_server_lts"))


class LinuxInstallGateV1Tests(unittest.TestCase):
    def test_blocked_without_approval_or_backup(self) -> None:
        gate = evaluate_install_gate(
            distro_profile_id="linux_mint",
            operator_approval=False,
            backup_verified=False,
            target_role="linux",
            iso_sha256_ok=True,
            disk_roles_bound=True,
        )
        self.assertFalse(gate["authorized"])
        self.assertIn("approval_or_backup_required", gate["blockers"])

    def test_authorized_with_backup(self) -> None:
        gate = evaluate_install_gate(
            distro_profile_id="linux_mint",
            operator_approval=False,
            backup_verified=True,
            target_role="linux",
            iso_sha256_ok=True,
            disk_roles_bound=True,
        )
        self.assertTrue(gate["authorized"])
        self.assertFalse(gate["executed"])

    def test_windows_write_forbidden(self) -> None:
        gate = evaluate_install_gate(
            distro_profile_id="linux_mint",
            operator_approval=True,
            backup_verified=True,
            target_role="windows",
            iso_sha256_ok=True,
            disk_roles_bound=True,
            windows_write_requested=True,
        )
        self.assertFalse(gate["authorized"])


class InstallDiagnosisV1Tests(unittest.TestCase):
    def test_bios_outdated(self) -> None:
        result = classify_install_diagnosis(bios_compare={"outdated": True}, nvme_count=2)
        self.assertIn("bios_outdated_likely", result["issue_codes"])

    def test_role_bind_required(self) -> None:
        result = classify_install_diagnosis(nvme_count=2, disk_roles_bound=False)
        self.assertIn("nvme_role_bind_required", result["issue_codes"])


class AsusMintOrchestrationV1Tests(unittest.TestCase):
    def test_dry_run_bundle(self) -> None:
        plan = build_asus_mint_orchestration_plan(
            windows_disk={"serial": "WINSERIAL001", "model": "WIN-SSD", "size_bytes": 10**12},
            linux_disk={"serial": "LINUXSERIAL02", "model": "LIN-SSD", "size_bytes": 10**12},
            iso_path="/media/iso/mint.iso",
            sha256_expected="abc",
            sha256_actual="abc",
            operator_approval=True,
            backup_verified=False,
        )
        self.assertEqual(plan["selected_distro"], "linux_mint")
        self.assertTrue(plan["live_session_no_umstecken"])
        self.assertEqual(plan["orchestration"], "dev_laptop")
        self.assertFalse(plan["execute"]["allowed"])
        self.assertNotEqual(plan["windows_target"]["serial_hash"], plan["linux_target"]["serial_hash"])

    def test_iso_mint_supported(self) -> None:
        iso = check_linux_iso(
            distro="linux-mint",
            version="22",
            iso_path="/tmp/x.iso",
            sha256_expected="deadbeef",
            sha256_actual="deadbeef",
        )
        self.assertTrue(iso["install_allowed"])

    def test_execute_gate_never_executes(self) -> None:
        result = linux_install_execute_gate(
            preflight={
                "status": "ready",
                "expires_at_epoch": 9_999_999_999,
                "gate": {"authorized": True},
            },
            confirm_identity=True,
            confirm_destructive=True,
            current_linux_serial_hash="a",
            expected_linux_serial_hash="a",
            current_machine_id="m",
            expected_machine_id="m",
        )
        self.assertEqual(result["status"], "handoff_authorized")
        self.assertFalse(result["executed"])


class NvmeIdentityV1Tests(unittest.TestCase):
    def test_serial_hashed_not_plaintext_in_identity_key_inputs(self) -> None:
        entry = normalize_nvme_entry({"serial": "SUPERSECRETSERIAL", "model": "X", "size_bytes": 100})
        self.assertEqual(entry["serial_hash"], hash_serial("SUPERSECRETSERIAL"))
        self.assertNotIn("SUPERSECRETSERIAL", entry["serial_masked"])


if __name__ == "__main__":
    unittest.main()
