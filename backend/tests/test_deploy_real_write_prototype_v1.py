"""Strenge Tests für den limitierten Real-Write-Prototyp (nur removable Testmedien)."""

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


class TestDeployRealWritePrototypeV1(unittest.TestCase):
    def setUp(self):
        os.environ["SETUPHELFER_ENABLE_REAL_WRITE"] = "1"
        # Muss unter deploy.image_inspect _ALLOWED_CACHE_PREFIXES liegen (./cache/deploy vom Backend-CWD).
        self._cache = _BACKEND / "cache" / "deploy"
        self._cache.mkdir(parents=True, exist_ok=True)
        fc_mod._DEPLOY_FINAL_CONFIRMATION_STORE.clear()
        fc_mod._DEPLOY_WRITE_SESSION_STORE.clear()
        mod._is_block_device = None

    def tearDown(self):
        mod._is_block_device = None
        if "SETUPHELFER_ENABLE_REAL_WRITE" in os.environ:
            del os.environ["SETUPHELFER_ENABLE_REAL_WRITE"]

    def _image_with_checksum(self, name: str, data: bytes) -> tuple[str, str]:
        p = self._cache / name
        p.write_bytes(data)
        h = hashlib.sha256(data).hexdigest()
        return str(p.resolve()), h

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
        self.assertEqual(created["code"], "DEPLOY_FINAL_CONFIRMATION_CREATED")
        fid = str(created["final_confirmation_id"])
        token = str(created["confirmation_token"])
        snap = created["target_snapshot"]
        return fid, token, snap

    def _proto_request(self, **kwargs) -> dict:
        target = kwargs["target_device"]
        image_path = kwargs["image_path"]
        chk = kwargs["expected_checksum"]
        inspect_result = kwargs.get("inspect_result") or _inspect_for_device(target)
        safety = kwargs.get("safety_summary") or _safety(target)
        fid, token, tsnap = self._bootstrap_fc(target, image_path)
        guard = rg_mod.build_real_write_snapshot(target, inspect_result, safety)
        if "guard_snapshot" in kwargs:
            guard = kwargs["guard_snapshot"]
        return {
            "target_device": target,
            "image_path": image_path,
            "expected_checksum": chk,
            "inspect_result": inspect_result,
            "safety_summary": safety,
            "write_harness_result": kwargs.get("write_harness_result") or _harness_ok(),
            "real_write_guard_result": kwargs.get("real_write_guard_result") or {"code": "DEPLOY_REAL_WRITE_READY"},
            "guard_snapshot": guard,
            "final_confirmation_id": kwargs.get("final_confirmation_id") or fid,
            "confirmation_token": kwargs.get("confirmation_token") or token,
            "target_snapshot": kwargs.get("target_snapshot") or tsnap,
        }

    def test_feature_flag_missing_blocked(self):
        del os.environ["SETUPHELFER_ENABLE_REAL_WRITE"]
        ip, chk = self._image_with_checksum("ff.img", b"abc")
        target = str(self._cache / "blk1")
        target_p = Path(target)
        target_p.write_bytes(b"\x00" * 16)
        req = self._proto_request(target_device=target, image_path=ip, expected_checksum=chk)
        out = mod.execute_deploy_real_write_prototype(req)
        self.assertEqual(out["code"], "DEPLOY_REAL_WRITE_FEATURE_DISABLED")

    def test_image_too_large_blocked(self):
        ip, chk = self._image_with_checksum("big.img", b"x")
        target = str(self._cache / "blk2")
        Path(target).write_bytes(b"\x00" * 8)
        req = self._proto_request(target_device=target, image_path=ip, expected_checksum=chk)
        huge = {
            "code": "DEPLOY_IMAGE_INSPECT_WARNING",
            "image": {"path": ip, "exists": True, "is_regular_file": True, "extension": ".img", "size_bytes": 600 * 1024 * 1024},
            "verification": {"checksum_checked": True, "checksum_expected": True, "checksum_ok": True},
            "compatibility": {},
            "warnings": [],
            "errors": [],
        }
        with patch.object(mod, "inspect_deploy_image", return_value=huge):
            out = mod.execute_deploy_real_write_prototype(req)
        self.assertEqual(out["code"], "DEPLOY_REAL_WRITE_IMAGE_TOO_LARGE")

    def test_mounted_recheck_blocked(self):
        ip, chk = self._image_with_checksum("m.img", b"\x01" * (2 * 1024 * 1024))
        target = str(self._cache / "blk3")
        Path(target).write_bytes(b"\x00" * (2 * 1024 * 1024))
        req = self._proto_request(target_device=target, image_path=ip, expected_checksum=chk)
        ok_v = mod.validate_test_device(target, req["inspect_result"], req["safety_summary"])
        bad_v = dict(ok_v)
        bad_v["eligible"] = False
        bad_v["reasons"] = ["DEPLOY_REAL_WRITE_BLOCKED_MOUNTED"]
        with patch.object(mod, "validate_test_device", side_effect=[ok_v, bad_v]):
            mod._is_block_device = lambda p: p == target
            out = mod.execute_deploy_real_write_prototype(req)
        self.assertEqual(out["code"], "DEPLOY_REAL_WRITE_BLOCKED")
        self.assertIn("DEPLOY_REAL_WRITE_BLOCKED_MOUNTED", out["errors"])

    def test_readonly_blocked(self):
        ip, chk = self._image_with_checksum("ro.img", b"\x02" * 4096)
        target = str(self._cache / "blk4")
        Path(target).write_bytes(b"\x00" * 8192)
        req = self._proto_request(target_device=target, image_path=ip, expected_checksum=chk)
        ok_v = mod.validate_test_device(target, req["inspect_result"], req["safety_summary"])
        bad_v = dict(ok_v)
        bad_v["eligible"] = False
        bad_v["reasons"] = ["DEPLOY_REAL_WRITE_BLOCKED_READONLY"]
        with patch.object(mod, "validate_test_device", side_effect=[ok_v, bad_v]):
            mod._is_block_device = lambda p: p == target
            out = mod.execute_deploy_real_write_prototype(req)
        self.assertEqual(out["code"], "DEPLOY_REAL_WRITE_BLOCKED")

    def test_fingerprint_mismatch_blocked(self):
        ip, chk = self._image_with_checksum("fp.img", b"x")
        target = str(self._cache / "blk5")
        Path(target).write_bytes(b"\x00" * 8)
        req = self._proto_request(target_device=target, image_path=ip, expected_checksum=chk)
        gs = dict(req["guard_snapshot"])
        gs["fingerprint"] = "0" * 64
        req["guard_snapshot"] = gs
        out = mod.execute_deploy_real_write_prototype(req)
        self.assertEqual(out["code"], "DEPLOY_REAL_WRITE_BLOCKED")

    def test_harness_proof_missing_blocked(self):
        ip, chk = self._image_with_checksum("h.img", b"y")
        target = str(self._cache / "blk6")
        Path(target).write_bytes(b"\x00" * 8)
        req = self._proto_request(target_device=target, image_path=ip, expected_checksum=chk, write_harness_result={})
        out = mod.execute_deploy_real_write_prototype(req)
        self.assertEqual(out["code"], "DEPLOY_REAL_WRITE_BLOCKED")

    def test_regular_file_not_block_device_blocked(self):
        ip, chk = self._image_with_checksum("nf.img", b"z")
        target = str(self._cache / "notblk")
        Path(target).write_bytes(b"\x00" * 8)
        req = self._proto_request(target_device=target, image_path=ip, expected_checksum=chk)
        out = mod.execute_deploy_real_write_prototype(req)
        self.assertEqual(out["code"], "DEPLOY_REAL_WRITE_BLOCKED")

    def test_verify_mismatch_failed(self):
        ip, chk = self._image_with_checksum("vm.img", b"\x03" * (64 * 1024))
        target = str(self._cache / "blk7")
        Path(target).write_bytes(b"\x00" * (128 * 1024))
        req = self._proto_request(target_device=target, image_path=ip, expected_checksum=chk)
        mod._is_block_device = lambda p: p == target
        bad_verify = {
            "verify_status": "mismatch",
            "bytes_verified": 1,
            "expected_sha256": "aa",
            "actual_sha256": "bb",
            "mismatch_offset": 0,
            "sha256_hex": "aa",
        }
        with patch.object(mod, "verify_written_range", return_value=("mismatch", bad_verify)):
            out = mod.execute_deploy_real_write_prototype(req)
        self.assertEqual(out["code"], "DEPLOY_REAL_WRITE_VERIFY_FAILED")
        self.assertEqual(out["verify"]["verify_status"], "mismatch")

    def test_successful_prototype_write_completed(self):
        ip, chk = self._image_with_checksum("ok.img", os.urandom(8 * 1024))
        target = str(self._cache / "blk8")
        Path(target).write_bytes(b"\x00" * (16 * 1024))
        req = self._proto_request(target_device=target, image_path=ip, expected_checksum=chk)
        mod._is_block_device = lambda p: p == target
        out = mod.execute_deploy_real_write_prototype(req)
        self.assertEqual(out["code"], "DEPLOY_REAL_WRITE_COMPLETED", msg=out)
        self.assertEqual(out["verify"]["verify_status"], "verified")
        self.assertEqual(out["bytes_written"], 8 * 1024)
        self.assertIsNotNone(out["verify"].get("sha256_hex"))

    def test_verify_written_range_mismatch_unit(self):
        a = self._cache / "va.bin"
        b = self._cache / "vb.bin"
        a.write_bytes(b"abc")
        b.write_bytes(b"abd")
        st, payload = mod.verify_written_range(str(a), str(b), 3)
        self.assertEqual(st, "mismatch")
        self.assertEqual(payload.get("verify_status"), "mismatch")
        self.assertIsNotNone(payload.get("mismatch_offset"))

    def test_no_subprocess_or_shell_in_module(self):
        src = (_BACKEND / "deploy" / "real_write_prototype.py").read_text(encoding="utf-8")
        banned = ("subprocess", "os.system", "system(", "popen", "shell=True")
        lower = src.lower()
        for b in banned:
            self.assertNotIn(b.lower(), lower, msg=f"unexpected {b!r}")

    def test_api_route_registered(self):
        try:
            from fastapi import FastAPI
        except ImportError:
            self.skipTest("fastapi nicht installiert")
        import deploy.routes as routes_mod

        app = FastAPI()
        app.include_router(routes_mod.router)
        routes = [getattr(r, "path", None) for r in app.routes]
        self.assertIn("/api/deploy/write/prototype", routes)


if __name__ == "__main__":
    unittest.main()
