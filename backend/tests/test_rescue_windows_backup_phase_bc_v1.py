"""Tests for Phase B Windows backup scope / verify and Phase C system-disk gate."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.rescue_msi_lab_auto_boot import (
    LAB_PHYSICAL_E2E_MENU_TITLE,
    patch_grub_cfg_for_msi_lab_auto_boot,
    patch_grub_cfg_for_msi_physical_e2e_boot,
)
from core.rescue_fat32_esp_usb_writer import generate_fat32_esp_grub_cfg
from core.rescue_phase_a_evidence_eval import evaluate_phase_a_physical_e2e
from core.rescue_system_disk_restore_execute import execute_system_disk_restore, preview_system_disk_restore
from core.rescue_system_disk_restore_gate import (
    build_system_disk_restore_control,
    evaluate_system_disk_restore_gate,
    write_system_disk_restore_control,
)
from core.rescue_windows_backup_execute import verify_windows_backup
from core.rescue_windows_backup_scope import (
    SCOPE_FULL,
    SCOPE_SELECTIVE_CUSTOM,
    SCOPE_SELECTIVE_PERSONAL,
    build_backup_scope_plan,
    normalize_backup_scope,
    validate_scope_against_target,
)


class WindowsBackupScopeTests(unittest.TestCase):
    def test_normalize_aliases(self) -> None:
        self.assertEqual(normalize_backup_scope("raw_image"), SCOPE_FULL)
        self.assertEqual(normalize_backup_scope("personal"), SCOPE_SELECTIVE_PERSONAL)
        self.assertEqual(normalize_backup_scope("custom"), SCOPE_SELECTIVE_CUSTOM)

    def test_selective_personal_paths(self) -> None:
        plan = build_backup_scope_plan(scope="selective_personal")
        self.assertEqual(plan["scope"], SCOPE_SELECTIVE_PERSONAL)
        self.assertTrue(any(p.endswith("/Documents") for p in plan["include_paths"]))
        self.assertEqual(plan["artifact_kind"], "selective_tar")

    def test_custom_requires_paths(self) -> None:
        plan = build_backup_scope_plan(scope="selective_custom", custom_paths=[])
        self.assertTrue(plan.get("errors"))

    def test_target_system_disk_blocked(self) -> None:
        plan = build_backup_scope_plan(scope="full")
        errs = validate_scope_against_target(scope_plan=plan, target_role="windows_system_disk")
        self.assertTrue(any(e["code"] == "target_not_external" for e in errs))


class WindowsBackupVerifyTests(unittest.TestCase):
    def test_verify_sha256(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "selective-backup.tar.gz"
            artifact.write_bytes(b"hello-backup")
            digest = verify_windows_backup({"artifact": str(artifact)})["sha256"]
            ok = verify_windows_backup({"artifact": str(artifact), "sha256": digest})
            self.assertTrue(ok["verify_passed"])
            bad = verify_windows_backup({"artifact": str(artifact), "sha256": "deadbeef"})
            self.assertFalse(bad["verify_passed"])


class SystemDiskRestoreGateTests(unittest.TestCase):
    def test_gate_requires_control_and_consent(self) -> None:
        missing = evaluate_system_disk_restore_gate(
            control=None,
            payload_version="1.10.0.37",
        )
        self.assertFalse(missing["allowed"])

        control = build_system_disk_restore_control(
            expected_payload_version="1.10.0.37",
            backup_artifact="/tmp/a.tar.gz",
        )
        blocked = evaluate_system_disk_restore_gate(
            control=control,
            payload_version="1.10.0.37",
            machine_vendor="Micro-Star International Co., Ltd.",
            machine_model="GE63 Raider 8RE",
            operator_consent="",
        )
        self.assertFalse(blocked["allowed"])
        self.assertIn("operator_consent_required", blocked["errors"])

        ok = evaluate_system_disk_restore_gate(
            control=control,
            payload_version="1.10.0.37",
            machine_vendor="Micro-Star International Co., Ltd.",
            machine_model="GE63 Raider 8RE",
            operator_consent="explicit",
        )
        self.assertTrue(ok["allowed"])

    def test_execute_blocked_without_rescue_boot(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SETUPHELFER_FORCE_RESCUE_BOOT", None)
            with patch("core.rescue_system_disk_restore_execute._booted_from_rescue", return_value=False):
                result = execute_system_disk_restore({"operator_consent": "explicit"})
        self.assertFalse(result["restore_executed"])
        self.assertEqual(result["code"], "not_rescue_boot")

    def test_preview_exposes_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            logs = Path(tmp)
            control = build_system_disk_restore_control(expected_payload_version="1.10.0.37")
            write_system_disk_restore_control(logs, control)
            with patch(
                "core.rescue_system_disk_restore_execute.load_system_disk_restore_control",
                return_value=control,
            ):
                preview = preview_system_disk_restore(
                    {
                        "payload_version": "1.10.0.37",
                        "machine_vendor": "Micro-Star International Co., Ltd.",
                        "machine_model": "GE63 Raider",
                        "operator_consent": "explicit",
                    }
                )
            self.assertTrue(preview["preview_only"])
            self.assertFalse(preview["restore_executed"])
            self.assertTrue(preview["gate"]["allowed"])


class PhaseAEvidenceEvalTests(unittest.TestCase):
    def test_pending_when_only_old_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            logs = Path(tmp)
            ctrl_dir = logs / "setuphelfer/e2e-live-001d"
            ctrl_dir.mkdir(parents=True)
            (ctrl_dir / "run-control.json").write_text(
                json.dumps(
                    {
                        "enabled": True,
                        "consumed": False,
                        "created_at": "2026-07-18T05:16:14Z",
                        "run_nonce": "abc",
                    }
                ),
                encoding="utf-8",
            )
            old = logs / "setuphelfer/evidence/e2e/old/e2e-result.json"
            old.parent.mkdir(parents=True)
            old.write_text(
                json.dumps({"status": "physical_rescue_backup_restore_e2e_passed"}),
                encoding="utf-8",
            )
            # Force old mtime before arming.
            os.utime(old, (1_700_000_000, 1_700_000_000))
            result = evaluate_phase_a_physical_e2e(logs)
            self.assertFalse(result["ok"])
            self.assertEqual(result["code"], "phase_a_pending_msi_boot")

    def test_pass_on_fresh_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            logs = Path(tmp)
            ctrl_dir = logs / "setuphelfer/e2e-live-001d"
            ctrl_dir.mkdir(parents=True)
            (ctrl_dir / "run-control.json").write_text(
                json.dumps(
                    {
                        "enabled": True,
                        "consumed": True,
                        "created_at": "2026-07-18T05:16:14Z",
                        "run_nonce": "abc",
                    }
                ),
                encoding="utf-8",
            )
            fresh = logs / "setuphelfer/evidence/e2e/new/auto-physical-e2e-result.json"
            fresh.parent.mkdir(parents=True)
            fresh.write_text(
                json.dumps({"status": "physical_rescue_backup_restore_e2e_passed", "ok": True}),
                encoding="utf-8",
            )
            result = evaluate_phase_a_physical_e2e(logs)
            self.assertTrue(result["ok"])
            self.assertEqual(result["code"], "phase_a_passed")


class PhysicalE2EGrubPatchTests(unittest.TestCase):
    def test_physical_patch_sets_e2e_flags(self) -> None:
        base = generate_fat32_esp_grub_cfg()
        patched = patch_grub_cfg_for_msi_physical_e2e_boot(base)
        self.assertIn(LAB_PHYSICAL_E2E_MENU_TITLE, patched)
        self.assertIn("setuphelfer_msi_e2e_auto=1", patched)
        self.assertIn("setuphelfer_auto_discovery=0", patched)
        restored = patch_grub_cfg_for_msi_lab_auto_boot(patched)
        self.assertIn("setuphelfer_auto_discovery=1", restored)
        self.assertIn("setuphelfer_msi_e2e_auto=0", restored)


if __name__ == "__main__":
    unittest.main()
