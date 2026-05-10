from __future__ import annotations

import hashlib
import json
import shutil
import unittest
from pathlib import Path

from deploy.runner_rescue_sandbox_controlled_copy import (
    build_rescue_sandbox_copy_execution_precheck,
    build_rescue_sandbox_copy_final_gate,
    build_rescue_sandbox_copy_seal,
    execute_rescue_sandbox_config_copy,
    execute_rescue_sandbox_runtime_copy,
    verify_rescue_sandbox_copy_results,
)

_REPO = Path(__file__).resolve().parents[2]
_BR = _REPO / "build" / "rescue"
_H = _REPO / "docs" / "evidence" / "runtime-results" / "handoff"
_MAN = _BR / "sandbox_root_manifest.json"
_CFG_PLAN = _BR / "sandbox_config_copy_plan.json"
_RT_PLAN = _BR / "sandbox_runtime_copy_plan.json"
_CFG_RES = _BR / "sandbox" / "manifests" / "config_copy_result.json"
_RT_RES = _BR / "sandbox" / "manifests" / "runtime_copy_result.json"
_SAFE = _H / "rescue_build_sandbox_safety.json"
_FIN = _H / "rescue_build_sandbox_final_gate.json"
_PC = _H / "rescue_sandbox_copy_execution_precheck.json"
_V = _H / "rescue_sandbox_copy_verify_result.json"
_SEAL = _BR / "sandbox" / "manifests" / "sandbox_copy.seal.json"
_FG = _H / "rescue_sandbox_copy_final_gate.json"
_BRAND = _H / "setuphelfer_branding_guard_check.json"
_ZERO = _H / "runtime_identifier_zero_state_verification.json"
_RUNNER = _REPO / "backend" / "deploy" / "runner_rescue_sandbox_controlled_copy.py"
_ROUTES = _REPO / "backend" / "deploy" / "routes.py"


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class DeployRunnerRescueSandboxControlledCopyV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _H.mkdir(parents=True, exist_ok=True)
        _BR.mkdir(parents=True, exist_ok=True)
        (_BR / "sandbox" / "config-copy").mkdir(parents=True, exist_ok=True)
        (_BR / "sandbox" / "runtime-copy").mkdir(parents=True, exist_ok=True)
        (_BR / "sandbox" / "manifests").mkdir(parents=True, exist_ok=True)
        (_BR / "debian-live").mkdir(parents=True, exist_ok=True)
        (_BR / "runtime").mkdir(parents=True, exist_ok=True)
        for _sub in ("config-copy", "runtime-copy"):
            sd = _BR / "sandbox" / _sub
            if sd.is_dir():
                shutil.rmtree(sd)
            sd.mkdir(parents=True, exist_ok=True)
        self._bak: dict[Path, bytes | None] = {}
        paths = (
            _MAN,
            _CFG_PLAN,
            _RT_PLAN,
            _CFG_RES,
            _RT_RES,
            _SAFE,
            _FIN,
            _PC,
            _V,
            _SEAL,
            _FG,
            _BRAND,
            _ZERO,
        )
        for p in paths:
            self._bak[p] = p.read_bytes() if p.exists() else None
            p.unlink(missing_ok=True)

    def tearDown(self) -> None:
        for p, b in self._bak.items():
            if b is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(b)

    def _write_gate_safe(self) -> None:
        _FIN.write_text(
            json.dumps(
                {
                    "gate_status": "ready",
                    "rescue_build_sandbox_final_gate_schema_version": 1,
                }
            ),
            encoding="utf-8",
        )
        _SAFE.write_text(
            json.dumps(
                {
                    "evaluation": {"rescue_build_sandbox_safety_eval_status": "ok"},
                    "rescue_build_sandbox_safety_schema_version": 1,
                }
            ),
            encoding="utf-8",
        )
        _MAN.write_text(
            json.dumps({"sandbox_root_manifest_schema_version": 1, "paths": []}),
            encoding="utf-8",
        )
        _BRAND.write_text(
            json.dumps({"branding_guard_status": "ok"}),
            encoding="utf-8",
        )
        _ZERO.write_text(
            json.dumps({"zero_state_status": "ok"}),
            encoding="utf-8",
        )

    def test_precheck_blocks_target_outside_sandbox(self) -> None:
        self._write_gate_safe()
        _CFG_PLAN.write_text(
            json.dumps(
                {
                    "plan_entries": [
                        {
                            "copy_mode": "readonly_copy",
                            "overwrite_allowed": False,
                            "source_path": "build/rescue/debian-live/a.json",
                            "target_path": "build/rescue/sandbox_config_bad/x.json",
                        }
                    ],
                    "sandbox_config_copy_plan_schema_version": 1,
                }
            ),
            encoding="utf-8",
        )
        _RT_PLAN.write_text(
            json.dumps({"plan_entries": [], "sandbox_runtime_copy_plan_schema_version": 1}),
            encoding="utf-8",
        )
        src = _BR / "debian-live" / "a.json"
        src.write_text('{"k":1}', encoding="utf-8")
        r = build_rescue_sandbox_copy_execution_precheck(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_sandbox_copy_execution_precheck_status"), "blocked")
        self.assertTrue(any("TGT_OUTSIDE" in x or "TARGET_PREFIX" in x for x in (r.get("errors") or [])))

    def test_precheck_blocks_symlink_escape(self) -> None:
        self._write_gate_safe()
        outside = _REPO / "tmp_sccopy_escape_target.json"
        outside.write_text("{}", encoding="utf-8")
        link = _BR / "debian-live" / "esc.json"
        link.unlink(missing_ok=True)
        link.symlink_to(outside)
        _CFG_PLAN.write_text(
            json.dumps(
                {
                    "plan_entries": [
                        {
                            "copy_mode": "readonly_copy",
                            "overwrite_allowed": False,
                            "source_path": "build/rescue/debian-live/esc.json",
                            "target_path": "build/rescue/sandbox/config-copy/esc.json",
                        }
                    ],
                    "sandbox_config_copy_plan_schema_version": 1,
                }
            ),
            encoding="utf-8",
        )
        _RT_PLAN.write_text(
            json.dumps({"plan_entries": [], "sandbox_runtime_copy_plan_schema_version": 1}),
            encoding="utf-8",
        )
        r = build_rescue_sandbox_copy_execution_precheck(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_sandbox_copy_execution_precheck_status"), "blocked")
        self.assertTrue(any("SYMLINK_ESCAPE" in x for x in (r.get("errors") or [])))
        link.unlink(missing_ok=True)
        outside.unlink(missing_ok=True)

    def test_config_copy_hash_match_and_runtime_copy_hash_match(self) -> None:
        self._write_gate_safe()
        src_c = _BR / "debian-live" / "c.json"
        src_c.write_text('{"cfg":true}', encoding="utf-8")
        tgt_c = "build/rescue/sandbox/config-copy/c.json"
        _CFG_PLAN.write_text(
            json.dumps(
                {
                    "plan_entries": [
                        {
                            "copy_mode": "readonly_copy",
                            "overwrite_allowed": False,
                            "source_path": "build/rescue/debian-live/c.json",
                            "target_path": tgt_c,
                        }
                    ],
                    "sandbox_config_copy_plan_schema_version": 1,
                }
            ),
            encoding="utf-8",
        )
        src_r = _BR / "runtime" / "r.json"
        src_r.write_text('{"rt":1}', encoding="utf-8")
        tgt_r = "build/rescue/sandbox/runtime-copy/r.json"
        _RT_PLAN.write_text(
            json.dumps(
                {
                    "plan_entries": [
                        {
                            "copy_mode": "readonly_copy",
                            "overwrite_allowed": False,
                            "source_path": "build/rescue/runtime/r.json",
                            "target_path": tgt_r,
                        }
                    ],
                    "sandbox_runtime_copy_plan_schema_version": 1,
                }
            ),
            encoding="utf-8",
        )
        rc = execute_rescue_sandbox_config_copy(explicit_overwrite=True)
        self.assertEqual(rc.get("rescue_sandbox_copy_config_status"), "ok")
        body_c = rc.get("rescue_sandbox_copy_config") or {}
        row = (body_c.get("copied") or [])[0]
        self.assertEqual(row.get("source_sha256"), row.get("target_sha256"))
        rr = execute_rescue_sandbox_runtime_copy(explicit_overwrite=True)
        self.assertEqual(rr.get("rescue_sandbox_copy_runtime_status"), "ok")
        body_r = rr.get("rescue_sandbox_copy_runtime") or {}
        row2 = (body_r.get("copied") or [])[0]
        self.assertEqual(row2.get("source_sha256"), row2.get("target_sha256"))

    def test_existing_file_without_explicit_overwrite_blocks(self) -> None:
        self._write_gate_safe()
        src = _BR / "debian-live" / "d.json"
        src.write_text("{}", encoding="utf-8")
        tgt = _BR / "sandbox" / "config-copy" / "d.json"
        tgt.write_text("old", encoding="utf-8")
        _CFG_PLAN.write_text(
            json.dumps(
                {
                    "plan_entries": [
                        {
                            "copy_mode": "readonly_copy",
                            "overwrite_allowed": False,
                            "source_path": "build/rescue/debian-live/d.json",
                            "target_path": "build/rescue/sandbox/config-copy/d.json",
                        }
                    ],
                    "sandbox_config_copy_plan_schema_version": 1,
                }
            ),
            encoding="utf-8",
        )
        _RT_PLAN.write_text(
            json.dumps({"plan_entries": [], "sandbox_runtime_copy_plan_schema_version": 1}),
            encoding="utf-8",
        )
        r = execute_rescue_sandbox_config_copy(explicit_overwrite=False)
        self.assertEqual(r.get("rescue_sandbox_copy_config_status"), "blocked")
        self.assertTrue(any("EXISTS" in x for x in (r.get("errors") or [])))

    def test_iso_blocked_in_precheck(self) -> None:
        self._write_gate_safe()
        _CFG_PLAN.write_text(
            json.dumps(
                {
                    "plan_entries": [
                        {
                            "copy_mode": "readonly_copy",
                            "overwrite_allowed": False,
                            "source_path": "build/rescue/debian-live/x.iso",
                            "target_path": "build/rescue/sandbox/config-copy/x.iso",
                        }
                    ],
                    "sandbox_config_copy_plan_schema_version": 1,
                }
            ),
            encoding="utf-8",
        )
        _RT_PLAN.write_text(
            json.dumps({"plan_entries": [], "sandbox_runtime_copy_plan_schema_version": 1}),
            encoding="utf-8",
        )
        fake = _BR / "debian-live" / "x.iso"
        fake.write_text("not", encoding="utf-8")
        r = build_rescue_sandbox_copy_execution_precheck(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_sandbox_copy_execution_precheck_status"), "blocked")
        self.assertTrue(any("BLOCKED_ARTIFACT" in x or ".iso" in x for x in (r.get("errors") or [])))
        fake.unlink()

    def test_qcow2_blocked_in_precheck(self) -> None:
        self._write_gate_safe()
        _CFG_PLAN.write_text(
            json.dumps(
                {
                    "plan_entries": [
                        {
                            "copy_mode": "readonly_copy",
                            "overwrite_allowed": False,
                            "source_path": "build/rescue/debian-live/disk.qcow2",
                            "target_path": "build/rescue/sandbox/config-copy/disk.qcow2",
                        }
                    ],
                    "sandbox_config_copy_plan_schema_version": 1,
                }
            ),
            encoding="utf-8",
        )
        _RT_PLAN.write_text(
            json.dumps({"plan_entries": [], "sandbox_runtime_copy_plan_schema_version": 1}),
            encoding="utf-8",
        )
        fake = _BR / "debian-live" / "disk.qcow2"
        fake.write_text("x", encoding="utf-8")
        r = build_rescue_sandbox_copy_execution_precheck(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_sandbox_copy_execution_precheck_status"), "blocked")
        self.assertTrue(any("qcow2" in x.lower() for x in (r.get("errors") or [])))
        fake.unlink()

    def test_verify_blocks_hash_mismatch(self) -> None:
        self._write_gate_safe()
        src = _BR / "debian-live" / "e.json"
        src.write_text('{"e":1}', encoding="utf-8")
        _CFG_PLAN.write_text(
            json.dumps(
                {
                    "plan_entries": [
                        {
                            "copy_mode": "readonly_copy",
                            "overwrite_allowed": False,
                            "source_path": "build/rescue/debian-live/e.json",
                            "target_path": "build/rescue/sandbox/config-copy/e.json",
                        }
                    ],
                    "sandbox_config_copy_plan_schema_version": 1,
                }
            ),
            encoding="utf-8",
        )
        _RT_PLAN.write_text(
            json.dumps({"plan_entries": [], "sandbox_runtime_copy_plan_schema_version": 1}),
            encoding="utf-8",
        )
        execute_rescue_sandbox_config_copy(explicit_overwrite=True)
        execute_rescue_sandbox_runtime_copy(explicit_overwrite=True)
        tgt = _BR / "sandbox" / "config-copy" / "e.json"
        tgt.write_text("corrupt", encoding="utf-8")
        v = verify_rescue_sandbox_copy_results(explicit_overwrite=True)
        self.assertEqual(v.get("rescue_sandbox_copy_verify_status"), "blocked")
        self.assertTrue(any("HASH" in x for x in (v.get("errors") or [])))

    def test_seal_raw_byte_hashes(self) -> None:
        self._write_gate_safe()
        src = _BR / "debian-live" / "f.json"
        src.write_text('{"f":2}', encoding="utf-8")
        _CFG_PLAN.write_text(
            json.dumps(
                {
                    "plan_entries": [
                        {
                            "copy_mode": "readonly_copy",
                            "overwrite_allowed": False,
                            "source_path": "build/rescue/debian-live/f.json",
                            "target_path": "build/rescue/sandbox/config-copy/f.json",
                        }
                    ],
                    "sandbox_config_copy_plan_schema_version": 1,
                }
            ),
            encoding="utf-8",
        )
        _RT_PLAN.write_text(
            json.dumps({"plan_entries": [], "sandbox_runtime_copy_plan_schema_version": 1}),
            encoding="utf-8",
        )
        execute_rescue_sandbox_config_copy(explicit_overwrite=True)
        execute_rescue_sandbox_runtime_copy(explicit_overwrite=True)
        verify_rescue_sandbox_copy_results(explicit_overwrite=True)
        s = build_rescue_sandbox_copy_seal(explicit_overwrite=True)
        self.assertIn(s.get("rescue_sandbox_copy_seal_status"), ("ok", "review_required"))
        self.assertTrue(s.get("rescue_sandbox_copy_seal_handoff_written"))
        body = s.get("rescue_sandbox_copy_seal") or {}
        h = body.get("hashes") or {}
        self.assertIn("config_copy_result_sha256", h)
        self.assertIn("verify_result_handoff_sha256", h)
        vraw = _V.read_bytes()
        self.assertEqual(h.get("verify_result_handoff_sha256"), _sha256_bytes(vraw))

    def test_final_gate_blocks_legacy_in_result_json(self) -> None:
        self._write_gate_safe()
        _CFG_PLAN.write_text(
            json.dumps({"plan_entries": [], "sandbox_config_copy_plan_schema_version": 1}),
            encoding="utf-8",
        )
        _RT_PLAN.write_text(
            json.dumps({"plan_entries": [], "sandbox_runtime_copy_plan_schema_version": 1}),
            encoding="utf-8",
        )
        _CFG_RES.write_text(
            json.dumps(
                {
                    "copied": [],
                    "config_copy_result_schema_version": 1,
                    "note": "x pi-installer y",
                    "rescue_sandbox_copy_config_status": "ok",
                }
            ),
            encoding="utf-8",
        )
        _RT_RES.write_text(
            json.dumps(
                {
                    "copied": [],
                    "rescue_sandbox_copy_runtime_status": "ok",
                    "runtime_copy_result_schema_version": 1,
                }
            ),
            encoding="utf-8",
        )
        _PC.write_text(
            json.dumps({"precheck_eval_status": "ok", "rescue_sandbox_copy_execution_precheck_schema_version": 1}),
            encoding="utf-8",
        )
        _V.write_text(
            json.dumps({"rescue_sandbox_copy_verify_result_schema_version": 1, "verify_eval_status": "ok"}),
            encoding="utf-8",
        )
        _SEAL.write_text(
            json.dumps(
                {
                    "hashes": {},
                    "sandbox_copy_seal_schema_version": 1,
                    "seal_status": "ok",
                }
            ),
            encoding="utf-8",
        )
        g = build_rescue_sandbox_copy_final_gate(explicit_overwrite=True)
        self.assertEqual(g.get("rescue_sandbox_copy_final_gate_status"), "blocked")
        self.assertTrue(any("LEGACY" in x for x in (g.get("errors") or [])))

    def test_runner_no_forbidden_calls(self) -> None:
        raw = _RUNNER.read_text(encoding="utf-8").lower()
        self.assertNotIn("subprocess", raw)
        self.assertNotIn("mount(", raw)
        self.assertNotIn("chroot(", raw)

    def test_routes_sandbox_copy_paths(self) -> None:
        txt = _ROUTES.read_text(encoding="utf-8")
        for path in (
            "/rescue/sandbox-copy/precheck",
            "/rescue/sandbox-copy/config",
            "/rescue/sandbox-copy/runtime",
            "/rescue/sandbox-copy/verify",
            "/rescue/sandbox-copy/seal",
            "/rescue/sandbox-copy/final-gate",
        ):
            self.assertIn(path, txt)
        self.assertNotIn("/rescue/sandbox-copy/chroot", txt)
        self.assertNotIn("/rescue/sandbox-copy/mount", txt)


if __name__ == "__main__":
    unittest.main()
