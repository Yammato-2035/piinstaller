from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_rescue_build_environment_emulation import (
    build_rescue_build_emulation_final_gate,
    build_rescue_build_emulation_seal,
    build_rescue_build_environment_snapshot,
    build_rescue_overlay_persistence_emulation,
    build_rescue_simulated_build_logs,
    build_rescue_simulated_build_outputs,
    build_rescue_simulated_build_workspace,
    verify_rescue_build_emulation,
)

_REPO = Path(__file__).resolve().parents[2]
_EM = _REPO / "build" / "rescue" / "emulation"
_H = _REPO / "docs" / "evidence" / "runtime-results" / "handoff"
_SN = _EM / "build_environment_snapshot.json"
_WS = _EM / "simulated_build_workspace.json"
_OUT = _EM / "simulated_build_outputs.json"
_LOG = _EM / "simulated_build_logs.json"
_OV = _EM / "overlay_persistence_emulation.json"
_SEAL = _EM / "build_emulation.seal.json"
_V = _H / "rescue_build_emulation_verify.json"
_FG = _H / "rescue_build_emulation_final_gate.json"
_SBC = _H / "rescue_sandbox_copy_final_gate.json"
_BRAND = _H / "setuphelfer_branding_guard_check.json"
_ZERO = _H / "runtime_identifier_zero_state_verification.json"
_RUNNER = _REPO / "backend" / "deploy" / "runner_rescue_build_environment_emulation.py"
_ROUTES = _REPO / "backend" / "deploy" / "routes.py"


class DeployRunnerRescueBuildEnvironmentEmulationV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _EM.mkdir(parents=True, exist_ok=True)
        _H.mkdir(parents=True, exist_ok=True)
        self._bak: dict[Path, bytes | None] = {}
        for p in (_SN, _WS, _OUT, _LOG, _OV, _SEAL, _V, _FG, _SBC):
            self._bak[p] = p.read_bytes() if p.exists() else None
            p.unlink(missing_ok=True)

    def tearDown(self) -> None:
        for p, b in self._bak.items():
            if b is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(b)

    def _write_min_deps(self) -> None:
        (_REPO / "build" / "rescue" / "sandbox_root_manifest.json").parent.mkdir(parents=True, exist_ok=True)
        m = _REPO / "build" / "rescue" / "sandbox_root_manifest.json"
        if not m.exists():
            m.write_text('{"sandbox_root_manifest_schema_version": 1}', encoding="utf-8")
        ovl = _REPO / "build" / "rescue" / "overlay_workspace_plan.json"
        if not ovl.exists():
            ovl.write_text('{"overlay_workspace_plan_schema_version": 1}', encoding="utf-8")

    def _write_handoffs_for_final_gate(self) -> None:
        _SBC.write_text(
            json.dumps({"gate_status": "ready", "rescue_sandbox_copy_final_gate_schema_version": 1}),
            encoding="utf-8",
        )
        _BRAND.write_text(json.dumps({"branding_guard_status": "ok"}), encoding="utf-8")
        _ZERO.write_text(json.dumps({"zero_state_status": "ok"}), encoding="utf-8")

    def test_snapshot_complete(self) -> None:
        self._write_min_deps()
        r = build_rescue_build_environment_snapshot(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_build_emulation_environment_snapshot_status"), "ok")
        body = r.get("rescue_build_emulation_environment_snapshot") or {}
        for k in (
            "sandbox_state",
            "runtime_bundle_state",
            "runtime_copy_state",
            "config_copy_state",
            "overlay_workspace_state",
            "readonly_flags",
        ):
            self.assertIn(k, body)
        self.assertTrue(body.get("no_real_build_execution"))

    def test_workspace_readonly_emulated(self) -> None:
        r = build_rescue_simulated_build_workspace(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_build_emulation_workspace_status"), "ok")
        body = r.get("rescue_build_emulation_workspace") or {}
        self.assertTrue(body.get("readonly_emulated"))

    def test_outputs_only_emulated_generated_false(self) -> None:
        r = build_rescue_simulated_build_outputs(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_build_emulation_outputs_status"), "ok")
        body = r.get("rescue_build_emulation_outputs") or {}
        for a in body.get("simulated_artifacts") or []:
            self.assertFalse(a.get("generated"))
            self.assertTrue(a.get("readonly_emulated"))
        names = " ".join(str(a.get("filename") or "") for a in body.get("simulated_artifacts") or [])
        self.assertNotRegex(names.lower(), r"\.iso\b")
        self.assertNotIn(".qcow2", names.lower())

    def test_verify_blocks_legacy(self) -> None:
        self._write_min_deps()
        build_rescue_build_environment_snapshot(explicit_overwrite=True)
        build_rescue_simulated_build_workspace(explicit_overwrite=True)
        build_rescue_simulated_build_outputs(explicit_overwrite=True)
        build_rescue_simulated_build_logs(explicit_overwrite=True)
        build_rescue_overlay_persistence_emulation(explicit_overwrite=True)
        snap = json.loads(_SN.read_text(encoding="utf-8"))
        snap["note"] = "x pi-installer y"
        _SN.write_text(json.dumps(snap), encoding="utf-8")
        v = verify_rescue_build_emulation(explicit_overwrite=True)
        self.assertEqual(v.get("rescue_build_emulation_verify_status"), "blocked")
        self.assertTrue(any("LEGACY" in x for x in (v.get("errors") or [])))

    def test_verify_blocks_real_artifact_file(self) -> None:
        self._write_min_deps()
        build_rescue_build_environment_snapshot(explicit_overwrite=True)
        build_rescue_simulated_build_workspace(explicit_overwrite=True)
        build_rescue_simulated_build_outputs(explicit_overwrite=True)
        build_rescue_simulated_build_logs(explicit_overwrite=True)
        build_rescue_overlay_persistence_emulation(explicit_overwrite=True)
        bad = _EM / "real_kernel.bin"
        bad.write_bytes(b"\x00\x01binary")
        try:
            v = verify_rescue_build_emulation(explicit_overwrite=True)
            self.assertEqual(v.get("rescue_build_emulation_verify_status"), "blocked")
            self.assertTrue(any("NON_JSON" in x for x in (v.get("errors") or [])))
        finally:
            bad.unlink(missing_ok=True)

    def test_seal_produces_hashes(self) -> None:
        self._write_min_deps()
        build_rescue_build_environment_snapshot(explicit_overwrite=True)
        build_rescue_simulated_build_workspace(explicit_overwrite=True)
        build_rescue_simulated_build_outputs(explicit_overwrite=True)
        build_rescue_simulated_build_logs(explicit_overwrite=True)
        build_rescue_overlay_persistence_emulation(explicit_overwrite=True)
        verify_rescue_build_emulation(explicit_overwrite=True)
        s = build_rescue_build_emulation_seal(explicit_overwrite=True)
        self.assertEqual(s.get("rescue_build_emulation_seal_status"), "ok")
        body = s.get("rescue_build_emulation_seal") or {}
        self.assertIn("bundle_sha256", body)
        self.assertIn("build_environment_snapshot_sha256", body.get("file_hashes") or {})

    def test_final_gate_blocked_missing_seal(self) -> None:
        self._write_min_deps()
        build_rescue_build_environment_snapshot(explicit_overwrite=True)
        build_rescue_simulated_build_workspace(explicit_overwrite=True)
        build_rescue_simulated_build_outputs(explicit_overwrite=True)
        build_rescue_simulated_build_logs(explicit_overwrite=True)
        build_rescue_overlay_persistence_emulation(explicit_overwrite=True)
        verify_rescue_build_emulation(explicit_overwrite=True)
        self._write_handoffs_for_final_gate()
        g = build_rescue_build_emulation_final_gate(explicit_overwrite=True)
        self.assertEqual(g.get("rescue_build_emulation_final_gate_status"), "blocked")
        self.assertTrue(any("SEAL_MISSING" in x for x in (g.get("errors") or [])))

    def test_runner_no_forbidden_calls(self) -> None:
        raw = _RUNNER.read_text(encoding="utf-8").lower()
        self.assertNotIn("subprocess", raw)
        self.assertNotIn("mount(", raw)
        self.assertNotIn("chroot(", raw)

    def test_routes_build_emulation_paths(self) -> None:
        txt = _ROUTES.read_text(encoding="utf-8")
        for path in (
            "/rescue/build-emulation/environment-snapshot",
            "/rescue/build-emulation/workspace",
            "/rescue/build-emulation/outputs",
            "/rescue/build-emulation/logs",
            "/rescue/build-emulation/overlay",
            "/rescue/build-emulation/verify",
            "/rescue/build-emulation/seal",
            "/rescue/build-emulation/final-gate",
        ):
            self.assertIn(path, txt)
        self.assertNotIn("/rescue/build-emulation/chroot", txt)
        self.assertNotIn("/rescue/build-emulation/publish", txt)


if __name__ == "__main__":
    unittest.main()
