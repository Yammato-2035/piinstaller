"""PI-RS-ASUS-WIN11-RETEST-005 automated contract tests."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
_repo = _backend.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core import rescue_install_readiness_dcc as dcc  # noqa: E402
from core import rescue_windows11_controlled_retest as retest  # noqa: E402

WIN = {
    "nvme_identity_hash": "6b45cc50d930d46e55b9d56e73b7540e03329164619069dd784a8273cb33d031",
    "serial_hash": "c637055cc164eacf318916954783d1a3abadef888e6c8e57715f67710395f6a0",
    "eui": "0025385a11b16304",
    "pci_path": "0000:00:02.4",
    "confirmed": True,
    "write_allowed": False,
}
LIN = {
    "nvme_identity_hash": "ed84d453078b002bb70e496cefbb1d4c18fd3b783c0e8483703a770cb087c94a",
    "serial_hash": "84d4cc6f1c6b0cb7a80b092f7fa2c9a18b238f3794415fc9b14883b21b4fd082",
    "eui": "0025385811911d10",
    "pci_path": "0000:00:02.3",
    "confirmed": True,
    "write_allowed": False,
}


class TargetBindingTests(unittest.TestCase):
    def test_windows_linux_different(self) -> None:
        b = retest.build_target_role_binding(
            machine_profile="asus_rog_gabriel",
            machine_fingerprint_hash="79396619c22d7b85a9fe12605be514de731c157ba349911edfa65df5017b38b9",
            windows_target=WIN,
            linux_target=LIN,
            operator_confirmed=True,
        )
        self.assertTrue(b["binding_ok"])
        self.assertFalse(b["same_device"])
        self.assertFalse(b["write_allowed"])
        v = retest.validate_target_role_binding(b)
        self.assertTrue(v["ok"])

    def test_same_hash_rejected(self) -> None:
        bad_lin = dict(LIN, nvme_identity_hash=WIN["nvme_identity_hash"])
        b = retest.build_target_role_binding(
            machine_profile="asus_rog_gabriel",
            machine_fingerprint_hash="fp",
            windows_target=WIN,
            linux_target=bad_lin,
            operator_confirmed=True,
        )
        self.assertTrue(b["same_device"])
        self.assertFalse(b["binding_ok"])


class IsolationTests(unittest.TestCase):
    def test_isolation_confirmed(self) -> None:
        iso = retest.build_linux_nvme_isolation(
            method="physical_remove",
            linux_identity_hash=LIN["nvme_identity_hash"],
            windows_identity_hash=WIN["nvme_identity_hash"],
            verified_in_winpe=True,
            linux_writable_for_setup=False,
            operator_documented=True,
        )
        self.assertTrue(iso["ok"])
        self.assertEqual(iso["status"], "isolated")

    def test_isolation_unverified_blocks(self) -> None:
        iso = retest.build_linux_nvme_isolation(
            method="unverified",
            linux_identity_hash=LIN["nvme_identity_hash"],
            windows_identity_hash=WIN["nvme_identity_hash"],
            verified_in_winpe=False,
            linux_writable_for_setup=True,
            operator_documented=False,
        )
        self.assertFalse(iso["ok"])
        self.assertEqual(iso["status"], "blocked_linux_nvme_isolation")


class WinpeCollectorTests(unittest.TestCase):
    def test_required_files(self) -> None:
        root = _repo / "scripts/rescue-live/image/SETUPHELFER_WIN_DIAG"
        missing = retest.assert_winpe_collector_files(root)
        self.assertEqual(missing, [])
        logs = (root / "collect-win11-setup-logs.cmd").read_text(encoding="utf-8", errors="replace")
        self.assertIn("SETUP_LOGS", logs)
        self.assertIn("A B C D E F", logs)
        self.assertIn("Panther", logs)
        self.assertIn("Rollback", logs)
        disk = (root / "collect-win11-disk-info.cmd").read_text(encoding="utf-8", errors="replace")
        self.assertIn("No partitioning commands were executed", disk)
        self.assertNotRegex(disk, r"(?im)^\s*clean\b")
        self.assertNotRegex(disk, r"(?im)^\s*format\b")
        self.assertNotRegex(disk, r"(?im)^\s*online disk\b")
        ps1 = (root / "collect-win11-setup-logs.ps1").read_text(encoding="utf-8", errors="replace")
        self.assertIn("Panther", ps1)
        self.assertIn("Rollback", ps1)


class MediaAndBiosTests(unittest.TestCase):
    def test_corrupt_media_blocks(self) -> None:
        m = retest.build_windows_media_result(source="official", status="corrupt")
        self.assertEqual(m["block_reason"], "blocked_install_media_corrupt")
        self.assertFalse(m["install_start_allowed"])

    def test_bios_331_baseline(self) -> None:
        b = retest.build_bios_331_baseline(windows_identity_hash=WIN["nvme_identity_hash"])
        self.assertEqual(b["installed_version"], "G513QM.331")
        self.assertFalse(b["flash_performed"])

    def test_bios335_wrong_model_blocked(self) -> None:
        g = retest.bios_335_update_gate(
            model="G713PI",
            board="G713PI",
            installed="G513QM.331",
            target="G513QM.335",
            official_ez_flash_file=True,
            checksum_documented=True,
            ac_power=True,
            battery_ok=True,
            no_running_install=True,
            operator_approved=True,
        )
        self.assertFalse(g["ok"])
        self.assertIn("wrong_model", g["blockers"])
        self.assertFalse(g["auto_flash"])

    def test_bios335_g513qm_ready(self) -> None:
        g = retest.bios_335_update_gate(
            model="ROG Strix G513QM",
            board="G513QM",
            installed="G513QM.331",
            target="G513QM.335",
            official_ez_flash_file=True,
            checksum_documented=True,
            ac_power=True,
            battery_ok=True,
            no_running_install=True,
            operator_approved=True,
        )
        self.assertTrue(g["ok"])
        self.assertFalse(g["auto_flash"])
        self.assertTrue(g["linux_flash_forbidden"])


class CausalityTests(unittest.TestCase):
    def test_ab_constants_ok_strongly_implicated(self) -> None:
        c = retest.evaluate_bios_causality(
            stage_a_result="failed",
            stage_b_result="passed",
            same_media=True,
            same_windows_nvme=True,
            same_linux_isolation=True,
            other_variables_changed=False,
        )
        self.assertTrue(c["bios_335_strongly_implicated"])
        self.assertFalse(c["sole_cause_claimed"])
        self.assertEqual(c["causality"], "strongly_implicated")

    def test_changed_media_inconclusive(self) -> None:
        c = retest.evaluate_bios_causality(
            stage_a_result="failed",
            stage_b_result="passed",
            same_media=False,
            same_windows_nvme=True,
            same_linux_isolation=True,
            other_variables_changed=False,
        )
        self.assertEqual(c["causality"], "inconclusive")

    def test_changed_nvme_inconclusive(self) -> None:
        c = retest.evaluate_bios_causality(
            stage_a_result="failed",
            stage_b_result="passed",
            same_media=True,
            same_windows_nvme=False,
            same_linux_isolation=True,
            other_variables_changed=False,
        )
        self.assertEqual(c["causality"], "inconclusive")

    def test_same_failure_both(self) -> None:
        c = retest.evaluate_bios_causality(
            stage_a_result="failed",
            stage_b_result="failed",
            same_media=True,
            same_windows_nvme=True,
            same_linux_isolation=True,
            other_variables_changed=False,
        )
        self.assertTrue(c["bios_unlikely_primary_cause"])

    def test_331_success(self) -> None:
        d = retest.decide_stage_a_outcome(install_succeeded=True, firmware_related=None)
        self.assertEqual(d["endstatus"], "windows_installed_on_bios_331")

    def test_331_firmware_fail(self) -> None:
        d = retest.decide_stage_a_outcome(install_succeeded=False, firmware_related=True)
        self.assertEqual(d["endstatus"], "ready_for_bios_335_controlled_update")


class PostcheckAndDccTests(unittest.TestCase):
    def test_linux_locked_until_postcheck(self) -> None:
        g = retest.windows_postcheck_to_linux_gate({"windows_booted": False})
        self.assertEqual(g["linux_install_gate"], "blocked")
        self.assertFalse(g["linux_write_allowed"])

    def test_postcheck_passes(self) -> None:
        g = retest.windows_postcheck_to_linux_gate(
            {
                "windows_booted": True,
                "oobe_or_intermediate_ok": True,
                "two_reboots_ok": True,
                "system_on_windows_nvme": True,
                "efi_on_windows_nvme": True,
                "linux_nvme_unchanged": True,
                "critical_disk_events": False,
                "whea_critical": False,
            }
        )
        self.assertEqual(g["linux_install_gate"], "ready_for_planning")

    def test_dcc_no_fake_green_on_started(self) -> None:
        block = retest.build_win11_retest_dcc(
            bios_installed="G513QM.331",
            bios_update_result=None,
            causality="not_tested",
            windows_media_status="valid",
            windows_target_short="6b45cc50d930",
            linux_isolated=True,
            setup_phase="started",
            error_code="",
            setupdiag="",
            install_result="started",
            postcheck="pending",
            linux_gate="blocked",
            endstatus="ready_for_windows_retest_bios331",
        )
        self.assertEqual(block["overall_tone"], "yellow")
        self.assertTrue(block["fake_green_guard"])

    def test_dcc_wrapper(self) -> None:
        block = dcc.build_win11_retest_005_dcc(
            bios_installed="G513QM.331",
            bios_update_result=None,
            causality="not_tested",
            windows_media_status="unknown_hash",
            windows_target_short="6b45cc50d930",
            linux_isolated=False,
            setup_phase="UNKNOWN",
            error_code="",
            setupdiag="",
            install_result="pending",
            postcheck="pending",
            linux_gate="blocked",
            endstatus="ready_for_windows_retest_bios331",
        )
        self.assertEqual(block["task_id"], retest.TASK_ID)

    def test_destructive_phrases(self) -> None:
        auth = retest.build_destructive_authorization(
            machine_fingerprint_hash="fp",
            windows_identity_hash=WIN["nvme_identity_hash"],
            boot_id="boot",
            preflight_id="pf",
            identity_phrase=retest.PHRASE_IDENTITY,
            destructive_phrase=retest.PHRASE_DESTRUCTIVE,
            linux_offline_ack=True,
            no_backup_ack=True,
            expires_at="2099-01-01T00:00:00Z",
        )
        self.assertTrue(auth["ok"])
        self.assertFalse(auth["write_allowed"])


class LocaleAndPayloadTests(unittest.TestCase):
    def test_four_locales(self) -> None:
        keys = [
            "rescue_retest_windows_media",
            "rescue_retest_linux_nvme_isolated",
            "rescue_retest_setup_logs_saving",
            "rescue_retest_bios_comparison",
            "rescue_retest_linux_still_locked",
        ]
        for loc in ("de-DE", "en-US", "fr-FR", "nl-NL"):
            path = _repo / f"scripts/rescue-live/image/locales/{loc}.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            for k in keys:
                self.assertIn(k, data, msg=f"{loc} missing {k}")

    def test_payload_flag(self) -> None:
        cfg = json.loads((_repo / "config/rescue_payload_version.json").read_text(encoding="utf-8"))
        self.assertTrue(cfg.get("pi_rs_asus_win11_retest_005"))
        self.assertEqual(cfg.get("rescue_payload_version"), "1.10.3.1")


if __name__ == "__main__":
    unittest.main()
