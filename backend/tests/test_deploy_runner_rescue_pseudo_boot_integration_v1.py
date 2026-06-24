from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_rescue_pseudo_boot_integration import (
    build_rescue_backend_health_integration,
    build_rescue_overlay_boot_strategy,
    build_rescue_pseudo_boot_final_readiness,
    build_rescue_pseudo_boot_manifest,
    build_rescue_recovery_ui_integration,
    build_rescue_service_startup_simulation,
    validate_rescue_pseudo_boot_safety,
)
from deploy.routes_source_aggregate import read_deploy_routes_aggregate

_REPO = Path(__file__).resolve().parents[2]
_BR = _REPO / "build" / "rescue"
_H = _REPO / "docs/evidence/runtime-results/handoff"
_RUNNER = _REPO / "backend/deploy/runner_rescue_pseudo_boot_integration.py"
_ROUTES = _REPO / "backend/deploy/routes.py"

_BUILD_JSON = (
    "pseudo_boot_manifest.json",
    "service_startup_simulation.json",
    "overlay_boot_strategy.json",
    "backend_health_integration.json",
    "recovery_ui_integration.json",
)


class DeployRunnerRescuePseudoBootIntegrationV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _H.mkdir(parents=True, exist_ok=True)
        _BR.mkdir(parents=True, exist_ok=True)
        self._backs: dict[Path, bytes | None] = {}
        for name in _BUILD_JSON:
            p = _BR / name
            self._backs[p] = p.read_bytes() if p.exists() else None
        for hname in (
            "rescue_pseudo_boot_safety_validation.json",
            "rescue_pseudo_boot_final_readiness.json",
            "rescue_artifact_readiness_gate.json",
            "setuphelfer_branding_guard_check.json",
            "runtime_identifier_zero_state_verification.json",
        ):
            p = _H / hname
            self._backs[p] = p.read_bytes() if p.exists() else None
        for p in self._backs:
            if p.parent == _H:
                p.unlink(missing_ok=True)

    def tearDown(self) -> None:
        for p, bak in self._backs.items():
            if bak is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(bak)

    def _run_all_pseudo_boot_builders(self) -> None:
        build_rescue_pseudo_boot_manifest(explicit_overwrite=True)
        build_rescue_service_startup_simulation(explicit_overwrite=True)
        build_rescue_overlay_boot_strategy(explicit_overwrite=True)
        build_rescue_backend_health_integration(explicit_overwrite=True)
        build_rescue_recovery_ui_integration(explicit_overwrite=True)

    def test_boot_order_nine_stages(self) -> None:
        r = build_rescue_pseudo_boot_manifest(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_pseudo_boot_manifest_status"), "ok")
        chain = (r.get("rescue_pseudo_boot_manifest") or {}).get("ordered_boot_chain") or []
        orders = [s.get("order") for s in chain]
        self.assertEqual(orders, list(range(1, 10)))

    def test_overlay_readonly_and_no_auto_persist(self) -> None:
        r = build_rescue_overlay_boot_strategy(explicit_overwrite=True)
        body = r.get("rescue_pseudo_boot_overlay_strategy") or {}
        self.assertTrue(body.get("readonly_lowerdir"))
        self.assertTrue(body.get("never_auto_target_disk_persistence"))
        self.assertTrue(body.get("persistence_disabled_by_default"))

    def test_overlay_no_bind_mount_claim(self) -> None:
        r = build_rescue_overlay_boot_strategy(explicit_overwrite=True)
        self.assertTrue((r.get("rescue_pseudo_boot_overlay_strategy") or {}).get("no_bind_mount_simulation"))

    def test_backend_health_detects_core_routes(self) -> None:
        r = build_rescue_backend_health_integration(explicit_overwrite=True)
        self.assertIn(r.get("rescue_pseudo_boot_backend_health_status"), ("ok", "review_required"))
        checks = (r.get("rescue_pseudo_boot_backend_health") or {}).get("checks") or {}
        self.assertTrue(checks.get("endpoint_api_version"))
        self.assertTrue(checks.get("recovery_routes"))

    def test_recovery_ui_surfaces(self) -> None:
        r = build_rescue_recovery_ui_integration(explicit_overwrite=True)
        self.assertIn(r.get("rescue_pseudo_boot_recovery_ui_status"), ("ok", "review_required", "blocked"))
        body = r.get("rescue_pseudo_boot_recovery_ui") or {}
        self.assertTrue(body.get("no_pi_installer_ui_rests"))
        self.assertTrue(body.get("inspect_run_has_rescue_api_refs"))
        rels = body.get("recovery_related_sources") or []
        self.assertGreater(len(rels), 0)

    def test_no_iso_img_under_build_rescue(self) -> None:
        from deploy.runner_rescue_io import ARTIFACT_SCAN_SKIP_TOP

        self._run_all_pseudo_boot_builders()
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
                self.fail(f"unexpected image file: {fp}")

    def test_runner_no_subprocess_qemu_systemctl(self) -> None:
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

    def test_routes_pseudo_boot_endpoints(self) -> None:
        txt = read_deploy_routes_aggregate()
        for n in (
            "/rescue/pseudo-boot/manifest",
            "/rescue/pseudo-boot/service-startup",
            "/rescue/pseudo-boot/overlay-strategy",
            "/rescue/pseudo-boot/backend-health",
            "/rescue/pseudo-boot/recovery-ui",
            "/rescue/pseudo-boot/safety-validation",
            "/rescue/pseudo-boot/final-readiness",
        ):
            self.assertIn(n, txt)

    def test_routes_no_forbidden_vm_iso_strings(self) -> None:
        low = read_deploy_routes_aggregate().lower()
        for bad in ("qemu-system", "vboxmanage", "grub-mkrescue", "xorriso", "publish-release"):
            self.assertNotIn(bad, low)

    def test_safety_validation_ok(self) -> None:
        r = validate_rescue_pseudo_boot_safety(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_pseudo_boot_safety_validation_status"), "ok")

    def test_final_readiness_ready(self) -> None:
        self._run_all_pseudo_boot_builders()
        validate_rescue_pseudo_boot_safety(explicit_overwrite=True)
        (_H / "rescue_artifact_readiness_gate.json").write_text(
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
        r = build_rescue_pseudo_boot_final_readiness(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_pseudo_boot_final_readiness_status"), "ready")

    def test_final_readiness_blocked_on_branding(self) -> None:
        self._run_all_pseudo_boot_builders()
        (_H / "rescue_artifact_readiness_gate.json").write_text(
            json.dumps({"gate_status": "ready"}),
            encoding="utf-8",
        )
        (_H / "setuphelfer_branding_guard_check.json").write_text(
            json.dumps({"branding_guard_status": "blocked"}),
            encoding="utf-8",
        )
        (_H / "runtime_identifier_zero_state_verification.json").write_text(
            json.dumps({"zero_state_status": "ok"}),
            encoding="utf-8",
        )
        r = build_rescue_pseudo_boot_final_readiness(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_pseudo_boot_final_readiness_status"), "blocked")
