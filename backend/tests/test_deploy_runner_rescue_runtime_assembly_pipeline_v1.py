from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_rescue_runtime_assembly_pipeline import (
    build_rescue_backend_runtime_assembly,
    build_rescue_frontend_runtime_assembly,
    build_rescue_offline_configuration_assembly,
    build_rescue_recovery_runtime_assembly,
    build_rescue_runtime_assembly_final_gate,
    build_rescue_runtime_root,
    build_rescue_startup_script_assembly,
    validate_rescue_runtime_assembly_safety,
)
from deploy.routes_source_aggregate import read_deploy_routes_aggregate

_REPO = Path(__file__).resolve().parents[2]
_BR = _REPO / "build" / "rescue"
_RT = _BR / "runtime"
_H = _REPO / "docs/evidence/runtime-results/handoff"
_RUNNER = _REPO / "backend/deploy/runner_rescue_runtime_assembly_pipeline.py"
_ROUTES = _REPO / "backend/deploy/routes.py"

_RUNTIME_DIRS = (
    "opt/setuphelfer",
    "etc/setuphelfer",
    "var/log/setuphelfer",
    "run/setuphelfer",
    "run/setuphelfer/evidence",
    "run/setuphelfer/recovery",
    "usr/share/setuphelfer/frontend",
    "boot",
    "EFI",
    "live",
)
_SCRIPTS = ("start-backend.sh", "start-frontend.sh", "start-recovery-ui.sh", "shutdown-safe.sh")


class DeployRunnerRescueRuntimeAssemblyPipelineV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _H.mkdir(parents=True, exist_ok=True)
        _BR.mkdir(parents=True, exist_ok=True)
        self._backs: dict[Path, bytes | None] = {}
        for rel in (
            "runtime/runtime_root_manifest.json",
            "runtime/backend_runtime_assembly.json",
            "runtime/frontend_runtime_assembly.json",
            "runtime/recovery_runtime_assembly.json",
            "runtime/offline_configuration_assembly.json",
            "runtime/startup_script_assembly.json",
        ):
            p = _BR / rel
            self._backs[p] = p.read_bytes() if p.exists() else None
        for h in (
            "rescue_runtime_assembly_final_gate.json",
            "rescue_runtime_assembly_safety.json",
            "rescue_pseudo_boot_final_readiness.json",
            "setuphelfer_branding_guard_check.json",
            "runtime_identifier_zero_state_verification.json",
        ):
            p = _H / h
            self._backs[p] = p.read_bytes() if p.exists() else None
        for p in self._backs:
            p.unlink(missing_ok=True)
        for s in _SCRIPTS:
            (_RT / "scripts" / s).unlink(missing_ok=True)

    def tearDown(self) -> None:
        for p, bak in self._backs.items():
            if bak is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(bak)

    def _run_all_runtime_builders(self) -> None:
        build_rescue_runtime_root(explicit_overwrite=True)
        build_rescue_backend_runtime_assembly(explicit_overwrite=True)
        build_rescue_frontend_runtime_assembly(explicit_overwrite=True)
        build_rescue_recovery_runtime_assembly(explicit_overwrite=True)
        build_rescue_offline_configuration_assembly(explicit_overwrite=True)
        build_rescue_startup_script_assembly(explicit_overwrite=True)

    def test_runtime_structure_complete(self) -> None:
        r = build_rescue_runtime_root(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_runtime_root_status"), "ok")
        for sub in _RUNTIME_DIRS:
            self.assertTrue((_RT / Path(sub) / ".setuphelfer_runtime_assembly_placeholder").is_file())

    def test_startup_scripts_templates(self) -> None:
        r = build_rescue_startup_script_assembly(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_runtime_startup_scripts_status"), "ok")
        for s in _SCRIPTS:
            p = _RT / "scripts" / s
            self.assertTrue(p.is_file())
            txt = p.read_text(encoding="utf-8")
            self.assertIn("TEMPLATE", txt)
            self.assertIn(":", txt)

    def test_offline_readonly_defaults(self) -> None:
        r = build_rescue_offline_configuration_assembly(explicit_overwrite=True)
        body = r.get("rescue_runtime_offline_config") or {}
        self.assertIn("readonly", str(body.get("readonly_config_strategy", "")).lower())
        rsf = body.get("recovery_safe_defaults") or {}
        self.assertFalse(rsf.get("auto_restore"))
        self.assertFalse(rsf.get("auto_repair"))

    def test_recovery_runtime_modules(self) -> None:
        r = build_rescue_recovery_runtime_assembly(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_runtime_recovery_status"), "ok")
        mods = (r.get("rescue_runtime_recovery") or {}).get("rescue_modules") or []
        self.assertGreater(len(mods), 0)

    def test_no_iso_img(self) -> None:
        from deploy.runner_rescue_io import ARTIFACT_SCAN_SKIP_TOP

        self._run_all_runtime_builders()
        for fp in _BR.rglob("*"):
            if not fp.is_file():
                continue
            try:
                rel = fp.relative_to(_BR)
                if not rel.parts:
                    continue
                if rel.parts[0] in ARTIFACT_SCAN_SKIP_TOP or rel.parts[0].startswith("."):
                    continue
                if len(rel.parts) == 1 and rel.name.lower().startswith("uefi-fat32-"):
                    continue
            except ValueError:
                pass
            if fp.suffix.lower() in (".iso", ".img"):
                self.fail(f"unexpected image: {fp}")

    def test_runner_no_subprocess_vm(self) -> None:
        raw = _RUNNER.read_text(encoding="utf-8").lower()
        for bad in (
            "subprocess",
            "os.system",
            "qemu-system",
            "vboxmanage",
            "chroot(",
            "mount --bind",
            "grub-mkrescue",
            "xorriso",
        ):
            self.assertNotIn(bad, raw)

    def test_routes_runtime_endpoints(self) -> None:
        txt = read_deploy_routes_aggregate()
        for n in (
            "/rescue/runtime/root",
            "/rescue/runtime/backend",
            "/rescue/runtime/frontend",
            "/rescue/runtime/recovery",
            "/rescue/runtime/offline-config",
            "/rescue/runtime/startup-scripts",
            "/rescue/runtime/final-gate",
            "/rescue/runtime/safety-validation",
        ):
            self.assertIn(n, txt)

    def test_routes_no_forbidden_publish(self) -> None:
        low = read_deploy_routes_aggregate().lower()
        self.assertNotIn("publish-release", low)
        self.assertNotIn("qemu-system", low)

    def test_safety_validation_ok(self) -> None:
        r = validate_rescue_runtime_assembly_safety(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_runtime_safety_validation_status"), "ok")

    def test_final_gate_ready(self) -> None:
        self._run_all_runtime_builders()
        (_H / "rescue_pseudo_boot_final_readiness.json").write_text(
            json.dumps({"gate_status": "ready"}),
            encoding="utf-8",
        )
        (_H / "setuphelfer_branding_guard_check.json").write_text(
            json.dumps({"branding_guard_status": "ok"}),
            encoding="utf-8",
        )
        (_H / "runtime_identifier_zero_state_verification.json").write_text(
            json.dumps({"zero_state_status": "ok"}),
            encoding="utf-8",
        )
        r = build_rescue_runtime_assembly_final_gate(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_runtime_final_gate_status"), "ready")
