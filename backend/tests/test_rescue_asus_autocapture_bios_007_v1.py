"""PI-RS-ASUS-AUTOCAPTURE-BIOS-007 unit tests."""

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

from core.asus_lab.auto_import import discover_runs, dispatch_auto_import, import_one_run  # noqa: E402
from core.asus_lab.bios_control import (  # noqa: E402
    build_bios_change_contract,
    build_capability_inventory,
    validate_change_against_inventory,
)
from core.asus_lab.boot_orchestrator import run_boot_orchestrator  # noqa: E402
from core.asus_lab.carrier_consistency import evaluate_carrier_consistency  # noqa: E402
from core.asus_lab.redaction_gate import evaluate_tree, scan_text  # noqa: E402
from core.asus_lab.run_context import generate_run_id, validate_run_id  # noqa: E402
from core.rescue_asus_lab_authorization import load_lab_target_profile  # noqa: E402


def _exact_identity() -> dict:
    prof = load_lab_target_profile()
    return {
        "manufacturer": "ASUSTeK COMPUTER INC.",
        "board_name": "G513QM",
        "product_name": "ROG Strix G513QM_G513QM",
        "machine_id": prof["machine_id"],
        "system_uuid_hash": prof["system_uuid_hash"],
    }


class RunIdTests(unittest.TestCase):
    def test_auto_run_id(self) -> None:
        rid = generate_run_id("win11-live-capture")
        self.assertTrue(validate_run_id(rid)["ok"])
        self.assertFalse(validate_run_id("unknown-norunid")["ok"])
        self.assertFalse(validate_run_id("hw-discovery-x")["ok"])


class CarrierTests(unittest.TestCase):
    def test_consistency_pass_fail(self) -> None:
        ok = evaluate_carrier_consistency(
            {"a": "1.10.4.0", "b": "1.10.4.0"}, expected_version="1.10.4.0"
        )
        self.assertEqual(ok["carrier_version_consistency"], "passed")
        bad = evaluate_carrier_consistency(
            {"a": "1.10.4.0", "b": "1.10.3.1"}, expected_version="1.10.4.0"
        )
        self.assertEqual(bad["carrier_version_consistency"], "failed")
        self.assertFalse(bad["stick_update_allowed"])


class RedactionTests(unittest.TestCase):
    def test_bitlocker_key_blocked(self) -> None:
        r = scan_text("key 123456-123456-123456-123456-123456-123456-123456-123456")
        self.assertEqual(r["status"], "blocked")

    def test_tree_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "ok.txt"
            p.write_text("hello\n", encoding="utf-8")
            self.assertEqual(evaluate_tree(Path(tmp))["status"], "clean")


class BiosTests(unittest.TestCase):
    def test_inventory_and_unsupported_block(self) -> None:
        inv = build_capability_inventory()
        self.assertTrue(inv["settings"])
        change = build_bios_change_contract(
            change_id="c1",
            setting="SecureBoot",
            old_value="Disabled",
            new_value="Enabled",
            reason="test",
            write_method="firmware_setup_ui",
            write_supported=False,
            bitlocker_recovery_risk=True,
        )
        self.assertTrue(change["bitlocker_recovery_risk"])
        self.assertFalse(change["bitlocker_mutation"])
        gate = validate_change_against_inventory(change, inv)
        self.assertTrue(gate["ok"])

    def test_missing_recovery_flag_blocked(self) -> None:
        inv = build_capability_inventory()
        change = build_bios_change_contract(
            change_id="c2",
            setting="SecureBoot",
            old_value="Disabled",
            new_value="Enabled",
            reason="test",
            write_method="firmware_setup_ui",
            write_supported=False,
            bitlocker_recovery_risk=False,
        )
        gate = validate_change_against_inventory(change, inv)
        self.assertFalse(gate["ok"])


class OrchestratorTests(unittest.TestCase):
    def test_orchestrator_happy_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Minimal repo carriers
            cfg = root / "config"
            cfg.mkdir()
            (cfg / "rescue_payload_version.json").write_text(
                json.dumps({"rescue_payload_version": "1.10.4.0"}) + "\n", encoding="utf-8"
            )
            (cfg / "version.json").write_text(
                json.dumps({"project_version": "1.9.21.2"}) + "\n", encoding="utf-8"
            )
            # Point load_lab_target_profile via real repo — orchestrator uses real profile path
            setup = root / "SETUP_LOGS"
            setup.mkdir()
            (setup / "SETUP_LOGS.TAG").write_text("1\n", encoding="utf-8")
            result = run_boot_orchestrator(
                repo_root=_REPO,
                setup_logs_candidates=[setup],
                observed_identity=_exact_identity(),
                run_type="full-lab-capture",
                boot_id="boot-test-1",
                skip_hardware_cmds=True,
            )
            self.assertTrue(result["ok"], result)
            self.assertTrue(Path(result["run_root"]).is_dir())
            self.assertTrue((Path(result["run_root"]) / "AUTO_IMPORT.READY").is_file())

    def test_msi_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            setup = Path(tmp) / "SETUP_LOGS"
            setup.mkdir()
            (setup / "SETUP_LOGS.TAG").write_text("1\n", encoding="utf-8")
            result = run_boot_orchestrator(
                repo_root=_REPO,
                setup_logs_candidates=[setup],
                observed_identity={"manufacturer": "Micro-Star", "board_name": "MS-16P5"},
                skip_hardware_cmds=True,
            )
            self.assertFalse(result["ok"])
            self.assertEqual(result["blocked_reason"], "identity_not_exact_match")


class AutoImportTests(unittest.TestCase):
    def test_discover_and_import_lab_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            setup = root / "SETUP_LOGS"
            run_id = generate_run_id("full-lab-capture")
            run_root = setup / "asus-lab-runs" / run_id
            run_root.mkdir(parents=True)
            (run_root / "AUTO_IMPORT.READY").write_text(run_id + "\n", encoding="utf-8")
            (setup / "SETUP_LOGS.TAG").write_text("1\n", encoding="utf-8")
            prof = load_lab_target_profile()
            (run_root / "machine_identity.json").write_text(
                json.dumps(_exact_identity()) + "\n", encoding="utf-8"
            )
            (run_root / "result").mkdir()
            (run_root / "result" / "run_context.json").write_text(
                json.dumps({"machine_id": prof["machine_id"], "run_id": run_id}) + "\n",
                encoding="utf-8",
            )
            found = discover_runs(setup)
            self.assertEqual(len(found), 1)
            repo = root / "repo"
            (repo / "docs/evidence/rescue/asus-autocapture-bios-007/physical_runs").mkdir(parents=True)
            # copy lab target for authorization load — uses real repo modules with real profile
            out = import_one_run(
                run=found[0],
                repo_root=_REPO,
                quarantine_root=root / "quarantine",
            )
            self.assertEqual(out["status"], "imported", out)
            # idempotent
            out2 = import_one_run(
                run=found[0],
                repo_root=_REPO,
                quarantine_root=root / "quarantine",
            )
            self.assertEqual(out2["status"], "already_imported")

    def test_secret_quarantine(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_id = generate_run_id("hw-discovery")
            run_root = root / run_id
            run_root.mkdir()
            (run_root / "secret.txt").write_text(
                "123456-123456-123456-123456-123456-123456-123456-123456\n", encoding="utf-8"
            )
            (run_root / "machine_identity.json").write_text(
                json.dumps(_exact_identity()) + "\n", encoding="utf-8"
            )
            out = import_one_run(
                run={"run_id": run_id, "run_root": str(run_root), "run_type": "hw-discovery"},
                repo_root=_REPO,
                quarantine_root=root / "quarantine",
            )
            self.assertEqual(out["status"], "quarantined")
            self.assertIn("secret_gate", out["reason"])


class PayloadFlagTests(unittest.TestCase):
    def test_payload_flag(self) -> None:
        cfg = json.loads((_REPO / "config/rescue_payload_version.json").read_text(encoding="utf-8"))
        self.assertEqual(cfg["rescue_payload_version"], "1.10.4.0")
        self.assertTrue(cfg.get("pi_rs_asus_autocapture_bios_007"))


if __name__ == "__main__":
    unittest.main()
