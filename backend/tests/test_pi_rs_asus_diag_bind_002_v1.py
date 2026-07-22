"""PI-RS-ASUS-DIAG-BIND-002 tests: identity import gate, run types, Gabriel bind."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core import rescue_bios_official_compare as bios  # noqa: E402
from core import rescue_evidence_import_identity as ident  # noqa: E402
from core import rescue_machine_identity_profiles as mid  # noqa: E402
from core import rescue_run_type_contract as rtype  # noqa: E402


class ImportIdentityGateTests(unittest.TestCase):
    def test_boot_id_required_no_newest_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # newest MSI session (wrong machine)
            msi = root / "rescue-session-msi"
            msi.mkdir()
            (msi / "00-session.json").write_text(
                json.dumps({"boot_id": "other-boot"}), encoding="utf-8"
            )
            (msi / "01-machine.json").write_text(
                json.dumps(
                    {
                        "vendor": "Micro-Star International Co., Ltd.",
                        "product_name": "GE63 Raider RGB 8RF",
                        "board_name": "MS-16P5",
                    }
                ),
                encoding="utf-8",
            )
            # matching ASUS session older
            asus = root / "rescue-session-asus"
            asus.mkdir()
            (asus / "00-session.json").write_text(
                json.dumps({"boot_id": "503549ad"}), encoding="utf-8"
            )
            (asus / "01-machine.json").write_text(
                json.dumps(
                    {
                        "vendor": "ASUSTeK COMPUTER INC.",
                        "product_name": "ROG Strix G513QM_G513QM",
                        "board_name": "G513QM",
                    }
                ),
                encoding="utf-8",
            )
            # Make MSI newer
            import os
            import time

            now = time.time()
            os.utime(msi, (now, now))
            os.utime(asus, (now - 100, now - 100))

            selected = ident.select_compatible_session(
                root,
                boot_id="503549ad",
                expected_manufacturer="ASUSTeK COMPUTER INC.",
                expected_board="G513QM",
                expected_product="ROG Strix G513QM",
            )
            self.assertTrue(selected["ok"])
            self.assertEqual(selected["session_id"], "rescue-session-asus")

            # Without matching boot — no session
            none_sel = ident.select_compatible_session(
                root,
                boot_id="missing-boot",
                expected_manufacturer="ASUSTeK COMPUTER INC.",
                expected_board="G513QM",
            )
            self.assertFalse(none_sel["ok"])
            self.assertTrue(any(c.get("reason") == "boot_id_mismatch" for c in none_sel["conflicts"]))

    def test_msi_rejected_for_asus_expectation(self) -> None:
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
        self.assertIn("msi_cannot_bind_asus_profile", check["reasons"])


class RunTypeTests(unittest.TestCase):
    def test_discovery_does_not_require_bvr_run_control(self) -> None:
        r = rtype.evaluate_run_control(
            declared_run_type="hardware_discovery",
            artifact={
                "boot_id": "x",
                "machine_fingerprint_hash": "y",
                "payload_version": "1.10.1.2",
            },
        )
        self.assertEqual(r["status"], "discovery_complete")
        self.assertFalse(r["run_control_invalid_correct"])

    def test_full_e2e_run_control_invalid_correct(self) -> None:
        r = rtype.evaluate_run_control(
            declared_run_type="full_e2e",
            artifact={
                "boot_id": "x",
                "run_id": "r",
                "payload_version": "1.10.1.2",
                "run_control": {"enabled": False, "consumed": True},
            },
        )
        self.assertTrue(r["run_control_invalid_correct"])
        self.assertEqual(r.get("code"), "run_control_invalid")


class BiosG513Tests(unittest.TestCase):
    def test_official_update_available_335(self) -> None:
        machine = mid.build_machine_identity(
            dmi={
                "sys_vendor": "ASUSTeK COMPUTER INC.",
                "product_name": "ROG Strix G513QM_G513QM",
                "board_name": "G513QM",
                "bios_version": "G513QM.331",
            }
        )
        result = bios.check_latest_official_bios(machine=machine, online=True)
        self.assertEqual(result["status"], "update_available")
        self.assertEqual(result["latest_official_version"], "G513QM.335")
        self.assertFalse(result["automatic_flash_allowed"])
        self.assertTrue(bios.is_official_source_url(result["official_support_url"]))


class GabrielBindTests(unittest.TestCase):
    def test_bind_g513qm_with_phrase(self) -> None:
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
        self.assertEqual(bound["binding"]["profile_id"], "asus_rog_gabriel")
        self.assertFalse(bound["binding"]["write_permissions"]["installation"])


if __name__ == "__main__":
    unittest.main()
