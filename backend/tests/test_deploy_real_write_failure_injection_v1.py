"""Failure-Injection und Device-Drift für real_write_prototype (nur Testmode)."""

from __future__ import annotations

import hashlib
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

import deploy.final_confirmation as fc_mod
import deploy.real_write_guard as rg_mod
import deploy.real_write_prototype as mod


def _harness_ok() -> dict:
    return {
        "execute_code": "DEPLOY_WRITE_HARNESS_COMPLETED",
        "sha256_matches": True,
        "single_use_code": "DEPLOY_WRITE_HARNESS_SESSION_ALREADY_USED",
        "host_changes_detected": False,
    }


def _safety(device: str) -> dict:
    return {"policy_code": "safety.summary.v1", "targets": [{"device": device, "reason_code": "SAFETY_EMPTY_DISK", "write_allowed": True}]}


def _inspect_for_device(dev: str) -> dict:
    part = f"{dev}-part1"
    return {
        "classification": {"system_type": "EMPTY"},
        "storage": {
            "devices_classified": [
                {
                    "device": dev,
                    "type": "disk",
                    "size": "64GB",
                    "transport": "usb",
                    "removable": True,
                    "ro": False,
                    "rotational": 0,
                    "model": "USB Flash",
                    "partitions": [{"device": part, "fstype": "exfat", "mountpoint": None}],
                }
            ]
        },
        "filesystems": {"detected": {}},
    }


def _write_plan() -> dict:
    return {"plan_status": "ok", "blocked_reasons": []}


def _write_exec_result(target: str, image_path: str, ws_id: str = "ws123456") -> dict:
    return {
        "code": "DEPLOY_WRITE_EXECUTE_READY",
        "write_session_id": ws_id,
        "target_device": target,
        "selected_profile": "DEPLOY_PROFILE_MINIMAL_LINUX",
        "image_path": image_path,
        "simulated_execution": [{"code": "DEPLOY_EXEC_WRITE_IMAGE", "status": "simulated"}],
    }


def _confirmations() -> list[str]:
    return [
        "CONFIRM_ALL_DATA_WILL_BE_DESTROYED",
        "CONFIRM_TARGET_DEVICE_AGAIN",
        "CONFIRM_NO_SYSTEM_DISK",
        "CONFIRM_NO_WINDOWS_DUALBOOT",
        "CONFIRM_IMAGE_AND_PROFILE_MATCH",
        "CONFIRM_FINAL_DEPLOY_DRYRUN",
    ]


class TestDeployRealWriteFailureInjectionV1(unittest.TestCase):
    def setUp(self):
        os.environ["SETUPHELFER_ENABLE_REAL_WRITE"] = "1"
        os.environ["SETUPHELFER_REAL_WRITE_TESTMODE"] = "1"
        self._cache = _BACKEND / "cache" / "deploy"
        self._cache.mkdir(parents=True, exist_ok=True)
        fc_mod._DEPLOY_FINAL_CONFIRMATION_STORE.clear()
        fc_mod._DEPLOY_WRITE_SESSION_STORE.clear()
        mod._is_block_device = None
        for k in (
            "FAIL_BEFORE_OPEN",
            "FAIL_AFTER_OPEN",
            "FAIL_AFTER_CHUNKS",
            "FAIL_VERIFY_MISMATCH",
            "SETUPHELFER_FAIL_VERIFY_DEVICE_PATH",
            "FAIL_DURING_FSYNC",
            "FAIL_DEVICE_CHANGED",
        ):
            os.environ.pop(k, None)

    def tearDown(self):
        mod._is_block_device = None
        for k in (
            "SETUPHELFER_ENABLE_REAL_WRITE",
            "SETUPHELFER_REAL_WRITE_TESTMODE",
            "FAIL_BEFORE_OPEN",
            "FAIL_AFTER_OPEN",
            "FAIL_AFTER_CHUNKS",
            "FAIL_VERIFY_MISMATCH",
            "SETUPHELFER_FAIL_VERIFY_DEVICE_PATH",
            "FAIL_DURING_FSYNC",
            "FAIL_DEVICE_CHANGED",
        ):
            os.environ.pop(k, None)

    def _image_with_checksum(self, name: str, data: bytes) -> tuple[str, str]:
        p = self._cache / name
        p.write_bytes(data)
        return str(p.resolve()), hashlib.sha256(data).hexdigest()

    def _bootstrap_fc(self, target: str, image_path: str) -> tuple[str, str, dict]:
        ws_id = "ws123456"
        fc_mod._DEPLOY_WRITE_SESSION_STORE[ws_id] = {
            "write_session_id": ws_id,
            "confirmation_token": "tok",
            "target_device": target,
            "selected_profile": "DEPLOY_PROFILE_MINIMAL_LINUX",
            "image_path": image_path,
            "write_plan_hash": "x",
            "required_confirmations": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
            "used": False,
        }
        created = fc_mod.create_final_confirmation_session(
            {
                "write_execute_result": _write_exec_result(target, image_path, ws_id),
                "write_plan": _write_plan(),
                "inspect_result": _inspect_for_device(target),
                "confirmations": _confirmations(),
            }
        )
        fid = str(created["final_confirmation_id"])
        token = str(created["confirmation_token"])
        snap = created["target_snapshot"]
        return fid, token, snap

    def _request(self, target: str, ip: str, chk: str) -> dict:
        inspect_result = _inspect_for_device(target)
        safety = _safety(target)
        fid, token, tsnap = self._bootstrap_fc(target, ip)
        guard = rg_mod.build_real_write_snapshot(target, inspect_result, safety)
        return {
            "target_device": target,
            "image_path": ip,
            "expected_checksum": chk,
            "inspect_result": inspect_result,
            "safety_summary": safety,
            "write_harness_result": _harness_ok(),
            "real_write_guard_result": {"code": "DEPLOY_REAL_WRITE_READY"},
            "guard_snapshot": guard,
            "final_confirmation_id": fid,
            "confirmation_token": token,
            "target_snapshot": tsnap,
        }

    def test_fail_before_open_clean_abort(self):
        os.environ["FAIL_BEFORE_OPEN"] = "1"
        data = b"\x05" * (3 * 1024 * 1024)
        ip, chk = self._image_with_checksum("fbo.img", data)
        target = str(self._cache / "fbo_dev")
        Path(target).write_bytes(b"\x00" * len(data))
        mod._is_block_device = lambda p: p == target
        out = mod.execute_deploy_real_write_prototype(self._request(target, ip, chk))
        self.assertEqual(out["code"], "DEPLOY_REAL_WRITE_ABORTED")
        self.assertIn("FAIL_BEFORE_OPEN", out["errors"])
        self.assertEqual(out["bytes_written"], 0)

    def test_fail_after_open_handle_closed(self):
        os.environ["FAIL_AFTER_OPEN"] = "1"
        data = b"\x06" * 4096
        ip, chk = self._image_with_checksum("fao.img", data)
        target = str(self._cache / "fao_dev")
        Path(target).write_bytes(b"\x00" * 8192)
        mod._is_block_device = lambda p: p == target
        out = mod.execute_deploy_real_write_prototype(self._request(target, ip, chk))
        self.assertEqual(out["code"], "DEPLOY_REAL_WRITE_ABORTED")
        self.assertIn("FAIL_AFTER_OPEN", out["errors"])
        Path(target).open("r+b").close()

    def test_fail_after_chunks_partial_verify_failed(self):
        os.environ["FAIL_AFTER_CHUNKS"] = "1"
        data = b"\x07" * (3 * 1024 * 1024)
        ip, chk = self._image_with_checksum("fac.img", data)
        target = str(self._cache / "fac_dev")
        Path(target).write_bytes(b"\x00" * len(data))
        mod._is_block_device = lambda p: p == target
        out = mod.execute_deploy_real_write_prototype(self._request(target, ip, chk))
        self.assertEqual(out["code"], "DEPLOY_REAL_WRITE_VERIFY_FAILED")
        self.assertLess(out["bytes_written"], len(data))
        self.assertIn(out["verify"]["verify_status"], ("failed", "mismatch"))

    def test_fail_verify_mismatch(self):
        data = b"\x08" * 2048
        ip, chk = self._image_with_checksum("fvm.img", data)
        wrong = self._cache / "wrong_read.bin"
        wrong.write_bytes(b"\xff" * len(data))
        os.environ["FAIL_VERIFY_MISMATCH"] = "1"
        os.environ["SETUPHELFER_FAIL_VERIFY_DEVICE_PATH"] = str(wrong.resolve())
        target = str(self._cache / "fvm_dev")
        Path(target).write_bytes(b"\x00" * len(data))
        mod._is_block_device = lambda p: p == target
        out = mod.execute_deploy_real_write_prototype(self._request(target, ip, chk))
        self.assertEqual(out["code"], "DEPLOY_REAL_WRITE_VERIFY_FAILED")
        self.assertEqual(out["verify"]["verify_status"], "mismatch")

    def test_fail_during_fsync_aborted(self):
        os.environ["FAIL_DURING_FSYNC"] = "1"
        data = b"\x09" * 1024
        ip, chk = self._image_with_checksum("ffs.img", data)
        target = str(self._cache / "ffs_dev")
        Path(target).write_bytes(b"\x00" * len(data))
        mod._is_block_device = lambda p: p == target
        out = mod.execute_deploy_real_write_prototype(self._request(target, ip, chk))
        self.assertEqual(out["code"], "DEPLOY_REAL_WRITE_ABORTED")

    def test_fail_device_changed_code(self):
        os.environ["FAIL_DEVICE_CHANGED"] = "1"
        data = b"\x0a" * 512
        ip, chk = self._image_with_checksum("fdc.img", data)
        target = str(self._cache / "fdc_dev")
        Path(target).write_bytes(b"\x00" * len(data))
        mod._is_block_device = lambda p: p == target
        out = mod.execute_deploy_real_write_prototype(self._request(target, ip, chk))
        self.assertEqual(out["code"], "DEPLOY_REAL_WRITE_FINGERPRINT_CHANGED")

    def test_readonly_flip_readonly_changed(self):
        data = b"\x0b" * 512
        ip, chk = self._image_with_checksum("rof.img", data)
        target = str(self._cache / "rof_dev")
        Path(target).write_bytes(b"\x00" * len(data))
        mod._is_block_device = lambda p: p == target
        req = self._request(target, ip, chk)
        ok = dict(mod._collect_drift_state(target, req["inspect_result"], req["safety_summary"]))
        bad = dict(ok)
        bad["readonly"] = True
        with patch.object(mod, "_collect_drift_state", side_effect=[ok, ok, ok, bad]):
            out = mod.execute_deploy_real_write_prototype(req)
        self.assertEqual(out["code"], "DEPLOY_REAL_WRITE_READONLY_CHANGED")

    def test_mounted_flip_target_remounted(self):
        data = b"\x0c" * 512
        ip, chk = self._image_with_checksum("mtf.img", data)
        target = str(self._cache / "mtf_dev")
        Path(target).write_bytes(b"\x00" * len(data))
        mod._is_block_device = lambda p: p == target
        req = self._request(target, ip, chk)
        ok = dict(mod._collect_drift_state(target, req["inspect_result"], req["safety_summary"]))
        bad = dict(ok)
        bad["mounted"] = True
        with patch.object(mod, "_collect_drift_state", side_effect=[ok, ok, ok, bad]):
            out = mod.execute_deploy_real_write_prototype(req)
        self.assertEqual(out["code"], "DEPLOY_REAL_WRITE_TARGET_REMOUNTED")

    def test_mutex_always_released(self):
        data = b"\x0d" * 512
        ip, chk = self._image_with_checksum("mtx.img", data)
        target = str(self._cache / "mtx_dev")
        Path(target).write_bytes(b"\x00" * len(data))
        mod._is_block_device = lambda p: p == target
        os.environ["FAIL_BEFORE_OPEN"] = "1"
        mod.execute_deploy_real_write_prototype(self._request(target, ip, chk))
        self.assertTrue(mod._PROTOTYPE_WRITE_LOCK.acquire(blocking=False))
        mod._PROTOTYPE_WRITE_LOCK.release()

    def test_mutex_busy_aborts(self):
        data = b"\x0e" * 512
        ip, chk = self._image_with_checksum("mbz.img", data)
        target = str(self._cache / "mbz_dev")
        Path(target).write_bytes(b"\x00" * len(data))
        mod._is_block_device = lambda p: p == target
        mod._PROTOTYPE_WRITE_LOCK.acquire()
        try:
            out = mod.execute_deploy_real_write_prototype(self._request(target, ip, chk))
            self.assertEqual(out["code"], "DEPLOY_REAL_WRITE_ABORTED")
        finally:
            mod._PROTOTYPE_WRITE_LOCK.release()

    def test_no_banned_syscalls_in_module(self):
        src = (_BACKEND / "deploy" / "real_write_prototype.py").read_text(encoding="utf-8")
        lower = src.lower()
        for b in ("subprocess", "os.system", "popen", "shell=true"):
            self.assertNotIn(b, lower, msg=b)

    def test_injection_ignored_without_testmode(self):
        os.environ.pop("SETUPHELFER_REAL_WRITE_TESTMODE", None)
        os.environ["FAIL_BEFORE_OPEN"] = "1"
        data = b"\x0f" * 1024
        ip, chk = self._image_with_checksum("ign.img", data)
        target = str(self._cache / "ign_dev")
        Path(target).write_bytes(b"\x00" * len(data))
        mod._is_block_device = lambda p: p == target
        out = mod.execute_deploy_real_write_prototype(self._request(target, ip, chk))
        self.assertEqual(out["code"], "DEPLOY_REAL_WRITE_COMPLETED")


if __name__ == "__main__":
    unittest.main()
