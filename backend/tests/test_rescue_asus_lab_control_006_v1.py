"""PI-RS-ASUS-LAB-CONTROL-006 unit tests."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
_REPO = _BACKEND.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from core.rescue_asus_lab_authorization import (  # noqa: E402
    PROFILE_ID,
    assert_action_allowed,
    evaluate_disk_fingerprint_gate,
    evaluate_machine_identity_match,
    load_lab_target_profile,
)
from core.rescue_bitlocker_mutation_guard import (  # noqa: E402
    evaluate_bitlocker_command_gate,
    redact_bitlocker_secrets,
)
from core.rescue_lab_job_contract import build_lab_job, validate_lab_job  # noqa: E402
from core.rescue_lab_job_store import cancel_job, get_job, put_job  # noqa: E402
from core.rescue_win11_live_capture import (  # noqa: E402
    finalize_capture_status,
    generate_win11_run_id,
    resolve_setup_logs_roots,
    validate_run_id,
    write_heartbeat,
    build_heartbeat,
)


class LabAuthTests(unittest.TestCase):
    def test_profile_loads(self) -> None:
        prof = load_lab_target_profile()
        self.assertEqual(prof["profile_id"], PROFILE_ID)
        self.assertFalse(prof["authorization"]["bitlocker_mutation"])

    def test_exact_match_grants(self) -> None:
        prof = load_lab_target_profile()
        observed = {
            "manufacturer": "ASUSTeK COMPUTER INC.",
            "board_name": "G513QM",
            "product_name": "ROG Strix G513QM_G513QM",
            "machine_id": prof["machine_id"],
            "system_uuid_hash": prof["system_uuid_hash"],
        }
        r = evaluate_machine_identity_match(observed=observed, profile=prof)
        self.assertEqual(r["match"], "exact_match")
        self.assertTrue(r["grants_usable"])
        self.assertFalse(r["bitlocker_mutation"])

    def test_msi_blocked(self) -> None:
        r = evaluate_machine_identity_match(
            observed={"manufacturer": "Micro-Star", "board_name": "MS-16P5", "product_name": "GE63"}
        )
        self.assertEqual(r["match"], "mismatch")
        self.assertFalse(r["grants_usable"])

    def test_developer_blocked(self) -> None:
        r = evaluate_machine_identity_match(
            observed={"manufacturer": "ASUS", "board_name": "G713PI", "product_name": "ROG"}
        )
        self.assertEqual(r["match"], "mismatch")

    def test_hostname_alone_insufficient(self) -> None:
        r = evaluate_machine_identity_match(
            observed={"manufacturer": "ASUS", "board_name": "G513QM", "product_name": "ROG", "hostname": "gabriel"}
        )
        self.assertEqual(r["match"], "partial_match")
        self.assertFalse(r["grants_usable"])

    def test_bitlocker_action_blocked_even_on_exact(self) -> None:
        prof = load_lab_target_profile()
        observed = {
            "manufacturer": "ASUSTeK COMPUTER INC.",
            "board_name": "G513QM",
            "product_name": "ROG Strix G513QM_G513QM",
            "machine_id": prof["machine_id"],
            "system_uuid_hash": prof["system_uuid_hash"],
        }
        match = evaluate_machine_identity_match(observed=observed, profile=prof)
        gate = assert_action_allowed(match_result=match, action="shell", bitlocker_mutation=True)
        self.assertFalse(gate["ok"])

    def test_changed_disk_fingerprint_blocks_write(self) -> None:
        import copy

        prof = copy.deepcopy(load_lab_target_profile())
        for d in prof["expected_internal_disks"]:
            d["confirmed"] = True
        observed = {
            "manufacturer": "ASUSTeK COMPUTER INC.",
            "board_name": "G513QM",
            "product_name": "ROG Strix G513QM_G513QM",
            "machine_id": prof["machine_id"],
            "system_uuid_hash": prof["system_uuid_hash"],
        }
        match = evaluate_machine_identity_match(observed=observed, profile=prof)
        wrong = [{"nvme_identity_hash": "deadbeef" * 8, "role": "linux_lab_nvme"}]
        gate = assert_action_allowed(
            match_result=match,
            action="mint_install",
            observed_disks=wrong,
            required_disk_role="linux_lab_nvme",
            profile=prof,
        )
        self.assertFalse(gate["ok"])
        self.assertEqual(gate["blocked_reason"], "disk_fingerprint_mismatch")

    def test_unconfirmed_roles_block_destructive(self) -> None:
        prof = load_lab_target_profile()
        observed = {
            "manufacturer": "ASUSTeK COMPUTER INC.",
            "board_name": "G513QM",
            "product_name": "ROG Strix G513QM_G513QM",
            "machine_id": prof["machine_id"],
            "system_uuid_hash": prof["system_uuid_hash"],
        }
        match = evaluate_machine_identity_match(observed=observed, profile=prof)
        disks = [
            {"nvme_identity_hash": d["nvme_identity_hash"]} for d in prof["expected_internal_disks"]
        ]
        gate = assert_action_allowed(
            match_result=match,
            action="repartition",
            observed_disks=disks,
        )
        self.assertFalse(gate["ok"])
        self.assertEqual(gate["blocked_reason"], "disk_roles_unconfirmed")

    def test_rescue_stick_label_rejected(self) -> None:
        g = evaluate_disk_fingerprint_gate(
            observed_disks=[{"nvme_identity_hash": "x", "label": "SETUP_LOGS"}]
        )
        self.assertFalse(g["ok"])
        self.assertIn("rescue_stick_excluded", g["reasons"])


class BitLockerGuardTests(unittest.TestCase):
    def test_manage_bde_blocked(self) -> None:
        g = evaluate_bitlocker_command_gate("manage-bde -off C:")
        self.assertTrue(g["blocked"])

    def test_enable_bitlocker_blocked(self) -> None:
        g = evaluate_bitlocker_command_gate("Enable-BitLocker -MountPoint C:")
        self.assertTrue(g["blocked"])

    def test_readonly_status_allowed(self) -> None:
        g = evaluate_bitlocker_command_gate("manage-bde -status C:")
        self.assertFalse(g["blocked"])

    def test_redact_recovery_key(self) -> None:
        text = redact_bitlocker_secrets("key 123456-123456-123456-123456-123456-123456-123456-123456")
        self.assertNotIn("123456-123456", text)


class LiveCaptureTests(unittest.TestCase):
    def test_run_id_format(self) -> None:
        rid = generate_win11_run_id()
        self.assertTrue(validate_run_id(rid)["ok"])
        self.assertFalse(validate_run_id("unknown-norunid")["ok"])
        self.assertFalse(validate_run_id("norunid")["ok"])

    def test_setup_logs_label_not_letter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "SETUP_LOGS"
            root.mkdir()
            (root / "SETUP_LOGS.TAG").write_text("1\n", encoding="utf-8")
            r = resolve_setup_logs_roots([root, Path(tmp) / "C"])
            self.assertTrue(r["setup_capture_ready"])

    def test_heartbeat_and_finalize(self) -> None:
        rid = generate_win11_run_id()
        hb = build_heartbeat(run_id=rid, files_copied=0)
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "hb.json"
            write_heartbeat(p, hb)
            self.assertTrue(p.is_file())
        fin = finalize_capture_status(run_id=rid, panther_files=0, rollback_files=0, heartbeats=1)
        self.assertEqual(fin["status"], "insufficient_evidence")
        fin2 = finalize_capture_status(run_id=rid, panther_files=2, rollback_files=0, heartbeats=3)
        self.assertEqual(fin2["status"], "evidence_collected")
        self.assertFalse(fin2["definitive_freeze_root_cause_known"])


class LabJobTests(unittest.TestCase):
    def test_signed_job_accept_reject(self) -> None:
        key = b"test-key-lab-006"
        prof = load_lab_target_profile()
        job = build_lab_job(
            action_type="diagnostic",
            risk_class="read_only",
            target_fingerprint=str(prof["machine_id"]),
            requested_by="tester",
            authorization_profile_hash="abc",
            signing_key=key,
        )
        observed = {
            "manufacturer": "ASUSTeK COMPUTER INC.",
            "board_name": "G513QM",
            "product_name": "ROG Strix G513QM_G513QM",
            "machine_id": prof["machine_id"],
            "system_uuid_hash": prof["system_uuid_hash"],
        }
        ok = validate_lab_job(job, observed_identity=observed, seen_nonces=set(), signing_key=key)
        self.assertTrue(ok["ok"])
        replay = validate_lab_job(
            job, observed_identity=observed, seen_nonces={job["nonce"]}, signing_key=key
        )
        self.assertFalse(replay["ok"])
        self.assertIn("nonce_replay", replay["reasons"])

    def test_wrong_profile_blocked(self) -> None:
        key = b"test-key-lab-006"
        prof = load_lab_target_profile()
        job = build_lab_job(
            action_type="shell",
            risk_class="controlled",
            target_fingerprint=str(prof["machine_id"]),
            requested_by="tester",
            authorization_profile_hash="abc",
            command="uname -a",
            signing_key=key,
        )
        job = dict(job)
        job["target_profile"] = "MSI_GE63_LAB"
        # resign would fail anyway; validation catches profile first after signature fail
        observed = {
            "manufacturer": "ASUSTeK COMPUTER INC.",
            "board_name": "G513QM",
            "product_name": "ROG Strix G513QM_G513QM",
            "machine_id": prof["machine_id"],
            "system_uuid_hash": prof["system_uuid_hash"],
        }
        bad = validate_lab_job(job, observed_identity=observed, seen_nonces=set(), signing_key=key)
        self.assertFalse(bad["ok"])

    def test_bitlocker_shell_blocked(self) -> None:
        key = b"test-key-lab-006"
        prof = load_lab_target_profile()
        with self.assertRaises(ValueError):
            build_lab_job(
                action_type="shell",
                risk_class="controlled",
                target_fingerprint=str(prof["machine_id"]),
                requested_by="tester",
                authorization_profile_hash="abc",
                command="x",
                bitlocker_mutation=True,
                signing_key=key,
            )
        job = build_lab_job(
            action_type="shell",
            risk_class="controlled",
            target_fingerprint=str(prof["machine_id"]),
            requested_by="tester",
            authorization_profile_hash="abc",
            command="Disable-BitLocker -MountPoint C:",
            signing_key=key,
        )
        observed = {
            "manufacturer": "ASUSTeK COMPUTER INC.",
            "board_name": "G513QM",
            "product_name": "ROG Strix G513QM_G513QM",
            "machine_id": prof["machine_id"],
            "system_uuid_hash": prof["system_uuid_hash"],
        }
        bad = validate_lab_job(job, observed_identity=observed, seen_nonces=set(), signing_key=key)
        self.assertFalse(bad["ok"])
        self.assertIn("bitlocker_mutation_forbidden", bad["reasons"])

    def test_expired_job_blocked(self) -> None:
        from datetime import datetime, timedelta, timezone

        key = b"test-key-lab-006"
        prof = load_lab_target_profile()
        job = build_lab_job(
            action_type="diagnostic",
            risk_class="read_only",
            target_fingerprint=str(prof["machine_id"]),
            requested_by="tester",
            authorization_profile_hash="abc",
            ttl_seconds=1,
            signing_key=key,
        )
        observed = {
            "manufacturer": "ASUSTeK COMPUTER INC.",
            "board_name": "G513QM",
            "product_name": "ROG Strix G513QM_G513QM",
            "machine_id": prof["machine_id"],
            "system_uuid_hash": prof["system_uuid_hash"],
        }
        future = datetime.now(timezone.utc) + timedelta(hours=2)
        bad = validate_lab_job(
            job, observed_identity=observed, seen_nonces=set(), signing_key=key, now=future
        )
        self.assertFalse(bad["ok"])
        self.assertIn("job_expired", bad["reasons"])

    def test_job_store_cancel_and_get(self) -> None:
        key = b"test-key-lab-006"
        prof = load_lab_target_profile()
        job = build_lab_job(
            action_type="diagnostic",
            risk_class="read_only",
            target_fingerprint=str(prof["machine_id"]),
            requested_by="tester",
            authorization_profile_hash="abc",
            run_id=generate_win11_run_id(),
            signing_key=key,
        )
        put_job(job)
        self.assertEqual(get_job(job["job_id"])["job_id"], job["job_id"])
        cancelled = cancel_job(job["job_id"])
        self.assertEqual(cancelled["state"], "cancelled")


class PayloadFlagTests(unittest.TestCase):
    def test_payload_flag(self) -> None:
        cfg = json.loads((_REPO / "config/rescue_payload_version.json").read_text(encoding="utf-8"))
        self.assertEqual(cfg["rescue_payload_version"], "1.10.3.1")
        self.assertEqual(cfg["previous_rescue_payload_version"], "1.10.3.0")
        self.assertTrue(cfg.get("pi_rs_asus_lab_control_006"))


if __name__ == "__main__":
    unittest.main()
