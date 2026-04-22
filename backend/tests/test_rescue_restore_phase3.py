"""Phase 3.N: Restore-Session, Hard-Stops, gestufte Ausführung (mocks, kein Produktiv-IO)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

try:
    from core.rescue_hardstop import RestoreHardStopContext, evaluate_restore_hardstops

    _HAS_HARDSTOP = True
except ModuleNotFoundError:
    _HAS_HARDSTOP = False
    evaluate_restore_hardstops = None
    RestoreHardStopContext = None

try:
    from models.diagnosis import RescueRestoreRequest
    from modules.rescue_restore_execute import run_rescue_restore
    from modules.rescue_restore_gate import validate_restore_preconditions

    _HAS = True
except ModuleNotFoundError:
    _HAS = False
    RescueRestoreRequest = None
    run_rescue_restore = None
    validate_restore_preconditions = None


@unittest.skipUnless(_HAS_HARDSTOP, "rescue_hardstop nicht importierbar")
class TestRescueHardstop(unittest.TestCase):
    def test_backup_changed(self):
        p = Path("/tmp/setuphelfer-test/hardstop_fake.tar.gz")
        ctx = RestoreHardStopContext(
            state={"backup_snapshot": {"size": 1, "mtime": 1.0}},
            backup_path=p,
            target_device=None,
            restore_risk_level="green",
            encryption_key_hex=None,
            runner=None,
        )
        with patch.object(Path, "stat", return_value=type("S", (), {"st_size": 2, "st_mtime": 1.0})()):
            codes = evaluate_restore_hardstops(ctx)
        self.assertIn("rescue.restore.backup_changed", codes)


@unittest.skipUnless(_HAS, "pydantic fehlt")
class TestRescueRestoreGate(unittest.TestCase):
    def test_confirmation_missing(self):
        ok, code, _ = validate_restore_preconditions(
            dry_run_token="x",
            backup_file="/tmp/setuphelfer-test/a.tar.gz",
            target_device=None,
            confirmation=False,
            risk_acknowledged=False,
            session_id="s",
        )
        self.assertFalse(ok)
        self.assertEqual(code, "rescue.restore.confirmation_missing")

    def test_session_missing(self):
        ok, code, _ = validate_restore_preconditions(
            dry_run_token="x",
            backup_file="/tmp/setuphelfer-test/a.tar.gz",
            target_device=None,
            confirmation=True,
            risk_acknowledged=False,
            session_id="",
        )
        self.assertFalse(ok)
        self.assertEqual(code, "rescue.restore.session_missing")


@unittest.skipUnless(_HAS, "pydantic fehlt")
class TestRescueRestoreExecuteMocked(unittest.TestCase):
    def _base_state(self) -> dict:
        return {
            "allow_restore": True,
            "created_at": "2099-01-01T00:00:00+00:00",
            "backup_file": "/tmp/setuphelfer-test/fake.tar.gz",
            "target_device": None,
            "restore_risk_level": "green",
            "restore_decision": "proceed_possible",
            "dryrun_mode": "dryrun",
            "dryrun_simulation_status": "DRYRUN_OK",
            "session_id": "sess-integration-test",
            "backup_snapshot": {"size": 100, "mtime": 1.0},
            "backup_requires_decryption": False,
        }

    def test_success_path_mocked(self):
        tgt = Path("/tmp/setuphelfer-rescue-restore-test/ut_p3_empty")
        tgt.mkdir(parents=True, exist_ok=True)
        req = RescueRestoreRequest(
            session_id="sess-integration-test",
            backup_id="/tmp/setuphelfer-test/fake.tar.gz",
            restore_target_directory=str(tgt),
            target_device=None,
            dry_run_token="tok",
            confirmation=True,
            risk_acknowledged=False,
            target_confirmation_text="RESTORE_NO_BLOCK_DEVICE",
        )
        state = self._base_state()
        fake_arch = Path("/tmp/setuphelfer-test/fake.tar.gz")

        with patch("modules.rescue_restore_execute.validate_restore_preconditions", return_value=(True, "ok", state)):
            with patch("modules.rescue_restore_execute.is_running_system_disk", return_value=False):
                with patch("modules.rescue_restore_execute.assert_backup_readable_path", return_value=fake_arch):
                    with patch("modules.rescue_restore_execute.assert_restore_live_target_directory", return_value=tgt):
                        with patch("modules.rescue_restore_execute.verify_basic", return_value=(True, "ok", None)):
                            with patch("modules.rescue_restore_execute.evaluate_restore_hardstops", return_value=[]):
                                with patch(
                                    "modules.rescue_restore_execute._prepare_archive_path",
                                    return_value=(fake_arch, None),
                                ):
                                    with patch(
                                        "modules.rescue_restore_execute.restore_files",
                                        return_value=(True, "ok", None),
                                    ):
                                        with patch("modules.rescue_restore_execute.consume_dry_run_grant"):
                                            with patch(
                                                "modules.rescue_restore_execute.simulate_boot_preconditions",
                                                return_value={"estimate": {"bootability_class": "BOOTABLE_LIKELY"}},
                                            ):
                                                with patch(
                                                    "modules.rescue_restore_execute.run_boot_repair_pipeline",
                                                    return_value={"performed": False, "codes": []},
                                                ):
                                                    with patch.object(Path, "stat", return_value=type("S", (), {"st_size": 100, "st_mtime": 1.0})()):
                                                        out = run_rescue_restore(req)
        self.assertEqual(out.status, "ok")
        self.assertEqual(out.result, "RESTORE_SUCCESS")
        self.assertTrue(out.bootable)

    def test_decrypt_prepare_fails(self):
        tgt = Path("/tmp/setuphelfer-rescue-restore-test/ut_p3_empty2")
        tgt.mkdir(parents=True, exist_ok=True)
        req = RescueRestoreRequest(
            session_id="sess-integration-test",
            backup_id="/tmp/setuphelfer-test/enc.bin",
            restore_target_directory=str(tgt),
            dry_run_token="t",
            confirmation=True,
            risk_acknowledged=True,
            target_confirmation_text="RESTORE_NO_BLOCK_DEVICE",
            encryption_key_hex="ab" * 32,
        )
        st = self._base_state()
        st["backup_file"] = req.backup_id
        st["restore_risk_level"] = "yellow"
        st["restore_decision"] = "proceed_with_explicit_risk_ack"
        st["backup_requires_decryption"] = True
        with patch("modules.rescue_restore_execute.validate_restore_preconditions", return_value=(True, "ok", st)):
            with patch("modules.rescue_restore_execute.is_running_system_disk", return_value=False):
                with patch("modules.rescue_restore_execute.assert_backup_readable_path", return_value=Path(req.backup_id)):
                    with patch("modules.rescue_restore_execute.assert_restore_live_target_directory", return_value=tgt):
                        with patch("modules.rescue_restore_execute.verify_basic", return_value=(True, "ok", None)):
                            with patch("modules.rescue_restore_execute.evaluate_restore_hardstops", return_value=[]):
                                with patch(
                                    "modules.rescue_restore_execute._prepare_archive_path",
                                    return_value=(None, "rescue.restore.RESTORE_KEY_INVALID"),
                                ):
                                    with patch.object(Path, "stat", return_value=type("S", (), {"st_size": 100, "st_mtime": 1.0})()):
                                        out = run_rescue_restore(req)
        self.assertEqual(out.status, "error")
        self.assertEqual(out.result, "RESTORE_BLOCKED")
        self.assertIn("rescue.restore.RESTORE_KEY_INVALID", out.codes)

    def test_hardstop_blocks(self):
        tgt = Path("/tmp/setuphelfer-rescue-restore-test/ut_p3_empty3")
        tgt.mkdir(parents=True, exist_ok=True)
        req = RescueRestoreRequest(
            session_id="sess-integration-test",
            backup_id="/tmp/setuphelfer-test/fake.tar.gz",
            restore_target_directory=str(tgt),
            dry_run_token="t",
            confirmation=True,
            risk_acknowledged=False,
            target_confirmation_text="RESTORE_NO_BLOCK_DEVICE",
        )
        st = self._base_state()
        with patch("modules.rescue_restore_execute.validate_restore_preconditions", return_value=(True, "ok", st)):
            with patch("modules.rescue_restore_execute.is_running_system_disk", return_value=False):
                with patch("modules.rescue_restore_execute.assert_backup_readable_path", return_value=Path(req.backup_id)):
                    with patch("modules.rescue_restore_execute.assert_restore_live_target_directory", return_value=tgt):
                        with patch("modules.rescue_restore_execute.verify_basic", return_value=(True, "ok", None)):
                            with patch(
                                "modules.rescue_restore_execute.evaluate_restore_hardstops",
                                return_value=["rescue.hardstop.source_equals_target"],
                            ):
                                with patch.object(Path, "stat", return_value=type("S", (), {"st_size": 100, "st_mtime": 1.0})()):
                                    out = run_rescue_restore(req)
        self.assertEqual(out.result, "RESTORE_BLOCKED")
        self.assertIn("rescue.hardstop.source_equals_target", out.codes)
