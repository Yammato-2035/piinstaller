from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_rescue_build_sandbox_preparation import (
    build_rescue_build_cleanup_plan,
    build_rescue_build_sandbox_final_gate,
    build_rescue_build_sandbox_root,
    build_rescue_overlay_workspace_plan,
    build_rescue_sandbox_config_copy_plan,
    build_rescue_sandbox_runtime_copy_plan,
    validate_rescue_build_sandbox_safety,
)

_REPO = Path(__file__).resolve().parents[2]
_BR = _REPO / "build" / "rescue"
_H = _REPO / "docs" / "evidence" / "runtime-results" / "handoff"
_MAN = _BR / "sandbox_root_manifest.json"
_CFG = _BR / "sandbox_config_copy_plan.json"
_RT = _BR / "sandbox_runtime_copy_plan.json"
_OVL = _BR / "overlay_workspace_plan.json"
_CL = _BR / "build_cleanup_plan.json"
_SAFE = _H / "rescue_build_sandbox_safety.json"
_FIN = _H / "rescue_build_sandbox_final_gate.json"
_RUNNER = _REPO / "backend" / "deploy" / "runner_rescue_build_sandbox_preparation.py"
_ROUTES = _REPO / "backend" / "deploy" / "routes.py"

_SUBS = (
    "sandbox/workspace",
    "sandbox/config-copy",
    "sandbox/runtime-copy",
    "sandbox/manifests",
    "sandbox/logs",
    "sandbox/tmp",
    "sandbox/overlay",
    "sandbox/rollback",
    "sandbox/readonly-markers",
)


class DeployRunnerRescueBuildSandboxPreparationV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _H.mkdir(parents=True, exist_ok=True)
        _BR.mkdir(parents=True, exist_ok=True)
        self._bak: dict[Path, bytes | None] = {}
        _extra = (
            _H / "rescue_dry_build_final_gate.json",
            _H / "rescue_dry_build_safety_validation.json",
            _H / "rescue_runtime_bundle_consistency_check.json",
            _H / "setuphelfer_branding_guard_check.json",
            _H / "runtime_identifier_zero_state_verification.json",
        )
        for p in (_MAN, _CFG, _RT, _OVL, _CL, _SAFE, _FIN, *_extra):
            self._bak[p] = p.read_bytes() if p.exists() else None
            p.unlink(missing_ok=True)

    def tearDown(self) -> None:
        for p, b in self._bak.items():
            if b is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(b)

    def test_sandbox_structure_complete(self) -> None:
        r = build_rescue_build_sandbox_root(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_build_sandbox_root_status"), "ok")
        for sub in _SUBS:
            self.assertTrue((_BR / sub).is_dir(), sub)
        self.assertTrue(_MAN.is_file())

    def test_config_copy_plan_text_only(self) -> None:
        build_rescue_build_sandbox_root(explicit_overwrite=True)
        r = build_rescue_sandbox_config_copy_plan(explicit_overwrite=True)
        self.assertIn(r.get("rescue_build_sandbox_config_copy_plan_status"), ("ok", "review_required"))
        body = r.get("rescue_build_sandbox_config_copy_plan") or {}
        self.assertTrue(body.get("text_and_manifest_only"))
        for e in body.get("plan_entries") or []:
            self.assertEqual(e.get("copy_mode"), "readonly_copy")
            self.assertFalse(e.get("overwrite_allowed"))

    def test_overlay_plan_no_mount_execution(self) -> None:
        build_rescue_build_sandbox_root(explicit_overwrite=True)
        r = build_rescue_overlay_workspace_plan(explicit_overwrite=True)
        body = r.get("rescue_build_sandbox_overlay_workspace_plan") or {}
        self.assertTrue(body.get("no_mount_execution"))
        self.assertTrue(body.get("readonly_runtime"))

    def test_cleanup_plan_not_destructive(self) -> None:
        build_rescue_build_sandbox_root(explicit_overwrite=True)
        r = build_rescue_build_cleanup_plan(explicit_overwrite=True)
        body = r.get("rescue_build_cleanup_plan") or {}
        self.assertFalse(body.get("destructive_cleanup"))
        self.assertTrue(body.get("no_rm_rf_in_runner"))

    def test_runner_no_mount_subprocess_chroot_strings(self) -> None:
        raw = _RUNNER.read_text(encoding="utf-8").lower()
        self.assertNotIn("mount(", raw)
        self.assertNotIn("chroot(", raw)
        self.assertNotIn("subprocess", raw)
        self.assertNotIn("rm -rf", raw)

    def test_runtime_plan_blocks_iso_path(self) -> None:
        build_rescue_build_sandbox_root(explicit_overwrite=True)
        rt = _BR / "runtime"
        rt.mkdir(parents=True, exist_ok=True)
        bad = rt / "probe.iso"
        bad.write_bytes(b"x")
        r = build_rescue_sandbox_runtime_copy_plan(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_build_sandbox_runtime_copy_plan_status"), "blocked")
        self.assertTrue(any("RESCUE_SB_RP_BLOCKED" in x for x in (r.get("errors") or [])))
        bad.unlink()

    def test_routes_build_sandbox_paths(self) -> None:
        txt = _ROUTES.read_text(encoding="utf-8")
        for n in (
            "/rescue/build-sandbox/root",
            "/rescue/build-sandbox/config-copy-plan",
            "/rescue/build-sandbox/runtime-copy-plan",
            "/rescue/build-sandbox/overlay-workspace-plan",
            "/rescue/build-sandbox/cleanup-plan",
            "/rescue/build-sandbox/safety-validation",
            "/rescue/build-sandbox/final-gate",
        ):
            self.assertIn(n, txt)

    def test_routes_no_forbidden_segments(self) -> None:
        low = _ROUTES.read_text(encoding="utf-8").lower()
        for bad in (
            "/rescue/build-sandbox/execute",
            "/rescue/build-sandbox/chroot",
            "/rescue/build-sandbox/qemu",
            "/rescue/build-sandbox/publish",
            "/rescue/build-sandbox/release",
        ):
            self.assertNotIn(bad, low)

    def test_safety_validation_ok(self) -> None:
        build_rescue_build_sandbox_root(explicit_overwrite=True)
        build_rescue_sandbox_config_copy_plan(explicit_overwrite=True)
        build_rescue_sandbox_runtime_copy_plan(explicit_overwrite=True)
        build_rescue_overlay_workspace_plan(explicit_overwrite=True)
        build_rescue_build_cleanup_plan(explicit_overwrite=True)
        r = validate_rescue_build_sandbox_safety(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_build_sandbox_safety_validation_status"), "ok")

    def test_final_gate_blocked_on_sandbox_safety(self) -> None:
        build_rescue_build_sandbox_root(explicit_overwrite=True)
        build_rescue_sandbox_config_copy_plan(explicit_overwrite=True)
        (_BR / "runtime").mkdir(parents=True, exist_ok=True)
        build_rescue_sandbox_runtime_copy_plan(explicit_overwrite=True)
        build_rescue_overlay_workspace_plan(explicit_overwrite=True)
        build_rescue_build_cleanup_plan(explicit_overwrite=True)
        for p, payload in (
            (_H / "rescue_runtime_bundle_consistency_check.json", {"consistency_status": "ok"}),
            (_H / "rescue_dry_build_final_gate.json", {"gate_status": "ready"}),
            (_H / "rescue_dry_build_safety_validation.json", {"evaluation": {"rescue_dry_build_safety_eval_status": "ok"}}),
            (_H / "setuphelfer_branding_guard_check.json", {"branding_guard_status": "ok"}),
            (_H / "runtime_identifier_zero_state_verification.json", {"zero_state_status": "ok"}),
        ):
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(payload), encoding="utf-8")
        _SAFE.write_text(
            json.dumps({"evaluation": {"rescue_build_sandbox_safety_eval_status": "blocked"}}),
            encoding="utf-8",
        )
        g = build_rescue_build_sandbox_final_gate(explicit_overwrite=True)
        self.assertEqual(g.get("rescue_build_sandbox_final_gate_status"), "blocked")
        self.assertIn("RESCUE_SB_FIN_SB_SAFE_BLOCKED", g.get("errors") or [])

    def test_final_gate_blocked_on_legacy_in_manifest(self) -> None:
        build_rescue_build_sandbox_root(explicit_overwrite=True)
        build_rescue_sandbox_config_copy_plan(explicit_overwrite=True)
        (_BR / "runtime").mkdir(parents=True, exist_ok=True)
        build_rescue_sandbox_runtime_copy_plan(explicit_overwrite=True)
        build_rescue_overlay_workspace_plan(explicit_overwrite=True)
        build_rescue_build_cleanup_plan(explicit_overwrite=True)
        man = json.loads(_MAN.read_text(encoding="utf-8"))
        man["note"] = "legacy pi-installer marker for test"
        _MAN.write_text(json.dumps(man), encoding="utf-8")
        for p, payload in (
            (_H / "rescue_runtime_bundle_consistency_check.json", {"consistency_status": "ok"}),
            (_H / "rescue_dry_build_final_gate.json", {"gate_status": "ready"}),
            (_H / "rescue_dry_build_safety_validation.json", {"evaluation": {"rescue_dry_build_safety_eval_status": "ok"}}),
            (_H / "setuphelfer_branding_guard_check.json", {"branding_guard_status": "ok"}),
            (_H / "runtime_identifier_zero_state_verification.json", {"zero_state_status": "ok"}),
        ):
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(payload), encoding="utf-8")
        _SAFE.write_text(
            json.dumps({"evaluation": {"rescue_build_sandbox_safety_eval_status": "ok"}}),
            encoding="utf-8",
        )
        g = build_rescue_build_sandbox_final_gate(explicit_overwrite=True)
        self.assertEqual(g.get("rescue_build_sandbox_final_gate_status"), "blocked")
        self.assertTrue(any("RESCUE_SB_FIN_LEGACY" in x for x in (g.get("errors") or [])))
