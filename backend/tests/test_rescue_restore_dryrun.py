"""Restore-Dry-Run-Pipeline (Phase 2) — Archive unter /tmp/setuphelfer-test."""

from __future__ import annotations

import shutil
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

try:
    from models.diagnosis import RestoreDryRunRequest
    from modules.backup_engine import create_file_backup
    from modules.rescue_restore_dryrun import run_restore_dryrun_pipeline

    _HAS = True
except ModuleNotFoundError:
    _HAS = False
    RestoreDryRunRequest = None
    create_file_backup = None
    run_restore_dryrun_pipeline = None


@unittest.skipUnless(_HAS, "Backend-Abhängigkeiten (pydantic) fehlen")
class TestRescueRestoreDryrun(unittest.TestCase):
    root = Path("/tmp/setuphelfer-test") / "ut_rescue_dryrun"

    def setUp(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self._vt = patch("modules.backup_engine.validate_backup_target")
        self._vt.start()
        self.addCleanup(self._vt.stop)

    def tearDown(self) -> None:
        if self.root.is_dir():
            shutil.rmtree(self.root, ignore_errors=True)

    def test_1_full_backup_dryrun_succeeds(self):
        case = self.root / "c1"
        tree = case / "tree"
        (tree / "boot").mkdir(parents=True)
        (tree / "boot" / "vmlinuz-test").write_text("k", encoding="utf-8")
        (tree / "boot" / "initrd.img-test").write_text("i", encoding="utf-8")
        (tree / "etc").mkdir(parents=True)
        (tree / "etc" / "fstab").write_text(
            "UUID=00000000-0000-0000-0000-000000000001 / ext4 defaults 0 1\n",
            encoding="utf-8",
        )
        arch = case / "full.tar.gz"
        res = create_file_backup(
            [tree / "boot", tree / "etc"],
            archive_path=arch,
            allowed_source_prefixes=(case,),
            allowed_output_prefixes=(case,),
        )
        self.assertTrue(res.ok, res.detail)
        req = RestoreDryRunRequest(backup_file=str(arch.resolve()), mode="dryrun")
        out = run_restore_dryrun_pipeline(req)
        self.assertEqual(out.status, "ok")
        self.assertEqual(out.backup_assessment.get("backup_class"), "BACKUP_OK")
        self.assertEqual(out.dryrun.get("simulation_status"), "DRYRUN_OK")
        self.assertIn(out.restore_risk_level, ("green", "yellow"))

    def test_2_target_capacity_red(self):
        case = self.root / "c2"
        tree = case / "t"
        (tree / "boot").mkdir(parents=True)
        (tree / "boot" / "vmlinuz-x").write_text("k", encoding="utf-8")
        (tree / "boot" / "initrd.img-x").write_text("i", encoding="utf-8")
        (tree / "etc").mkdir(parents=True)
        (tree / "etc" / "fstab").write_text("proc /proc proc defaults 0 0\n", encoding="utf-8")
        arch = case / "full.tar.gz"
        res = create_file_backup(
            [tree / "boot", tree / "etc"],
            archive_path=arch,
            allowed_source_prefixes=(case,),
            allowed_output_prefixes=(case,),
        )
        self.assertTrue(res.ok, res.detail)
        req = RestoreDryRunRequest(backup_file=str(arch.resolve()), target_device="/dev/sda", mode="dryrun")
        with patch("modules.rescue_target_assessment.compare_backup_to_target") as m:
            m.return_value = {
                "capacity_ok": False,
                "codes": ["rescue.target.capacity_insufficient"],
                "backup_uncompressed_estimate_bytes": 10**15,
                "target_size_bytes": 1,
            }
            out = run_restore_dryrun_pipeline(req)
        self.assertEqual(out.restore_risk_level, "red")
        self.assertEqual(out.restore_decision, "recommend_new_target_disk")

    def test_3_encrypted_no_key(self):
        p = self.root / "x.tar.gz.gpg"
        p.write_bytes(b"x")
        req = RestoreDryRunRequest(backup_file=str(p.resolve()), mode="analyze_only")
        out = run_restore_dryrun_pipeline(req)
        self.assertEqual(out.backup_assessment.get("backup_class"), "BACKUP_ENCRYPTED_KEY_REQUIRED")
        self.assertEqual(out.restore_decision, "do_not_restore")

    def test_4_incremental_blocked(self):
        case = self.root / "c4"
        tree = case / "t"
        (tree / "a").mkdir(parents=True)
        (tree / "a" / "f.txt").write_text("x", encoding="utf-8")
        arch = case / "pi-backup-inc-rule-20990101.tar.gz"
        res = create_file_backup(
            [tree / "a"],
            archive_path=arch,
            allowed_source_prefixes=(case,),
            allowed_output_prefixes=(case,),
        )
        self.assertTrue(res.ok, res.detail)
        req = RestoreDryRunRequest(backup_file=str(arch.resolve()), mode="analyze_only")
        out = run_restore_dryrun_pipeline(req)
        self.assertEqual(out.backup_assessment.get("backup_class"), "BACKUP_WARN_INCOMPLETE")
        self.assertEqual(out.restore_decision, "do_not_restore")

    def test_5_boot_uncertain_minimal_tree(self):
        case = self.root / "c5"
        tree = case / "t"
        (tree / "etc").mkdir(parents=True)
        (tree / "etc" / "hosts").write_text("127.0.0.1 localhost\n", encoding="utf-8")
        arch = case / "mini.tar.gz"
        res = create_file_backup(
            [tree / "etc"],
            archive_path=arch,
            allowed_source_prefixes=(case,),
            allowed_output_prefixes=(case,),
        )
        self.assertTrue(res.ok, res.detail)
        req = RestoreDryRunRequest(backup_file=str(arch.resolve()), mode="dryrun")
        out = run_restore_dryrun_pipeline(req)
        self.assertEqual(out.dryrun.get("simulation_status"), "DRYRUN_OK")
        est = (out.bootability or {}).get("estimate") or {}
        self.assertIn(est.get("bootability_class"), ("BOOTABLE_UNCERTAIN", "BOOTABLE_UNLIKELY"))
