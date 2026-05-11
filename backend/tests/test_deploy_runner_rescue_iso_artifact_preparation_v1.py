from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path

from deploy.runner_rescue_iso_artifact_preparation import (
    build_offline_frontend_artifacts,
    build_rescue_artifact_readiness_gate,
    build_rescue_backend_artifacts,
    build_rescue_boot_artifact_structure,
    build_rescue_overlay_persistence_strategy,
    build_rescue_rootfs_artifact,
)

_REPO = Path(__file__).resolve().parents[2]
_BR = _REPO / "build" / "rescue"
_H = _REPO / "docs/evidence/runtime-results/handoff"
_ART_RUNNER = _REPO / "backend/deploy/runner_rescue_iso_artifact_preparation.py"
_ROUTES = _REPO / "backend/deploy/routes.py"


class DeployRunnerRescueIsoArtifactPreparationV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _H.mkdir(parents=True, exist_ok=True)
        _BR.mkdir(parents=True, exist_ok=True)
        self._gate_bak = (_H / "rescue_artifact_readiness_gate.json").read_bytes() if (_H / "rescue_artifact_readiness_gate.json").exists() else None
        self._iso_final_bak = (_H / "rescue_iso_final_readiness_gate.json").read_bytes() if (_H / "rescue_iso_final_readiness_gate.json").exists() else None
        self._brand_bak = (_H / "setuphelfer_branding_guard_check.json").read_bytes() if (_H / "setuphelfer_branding_guard_check.json").exists() else None
        (_H / "rescue_artifact_readiness_gate.json").unlink(missing_ok=True)

    def tearDown(self) -> None:
        for p, bak in (
            (_H / "rescue_artifact_readiness_gate.json", self._gate_bak),
            (_H / "rescue_iso_final_readiness_gate.json", self._iso_final_bak),
            (_H / "setuphelfer_branding_guard_check.json", self._brand_bak),
        ):
            if bak is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(bak)
        for name in (
            "rootfs_manifest.json",
            "frontend_manifest.json",
            "backend_manifest.json",
            "boot_artifact_manifest.json",
            "overlay_persistence_strategy.json",
        ):
            (_BR / name).unlink(missing_ok=True)
        shutil.rmtree(_BR / "rootfs", ignore_errors=True)
        shutil.rmtree(_BR / "boot", ignore_errors=True)
        shutil.rmtree(_BR / "EFI", ignore_errors=True)
        shutil.rmtree(_BR / "live", ignore_errors=True)

    def _run_all_artifacts(self) -> None:
        build_rescue_rootfs_artifact(explicit_overwrite=True)
        build_offline_frontend_artifacts(explicit_overwrite=True)
        build_rescue_backend_artifacts(explicit_overwrite=True)
        build_rescue_boot_artifact_structure(explicit_overwrite=True)
        build_rescue_overlay_persistence_strategy(explicit_overwrite=True)

    def test_rootfs_layout_complete(self) -> None:
        r = build_rescue_rootfs_artifact(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_artifact_rootfs_status"), "ok")
        for sub in (
            "opt/setuphelfer",
            "etc/setuphelfer",
            "var/log/setuphelfer",
            "usr/share/setuphelfer/frontend",
            "run/setuphelfer/evidence",
            "run/setuphelfer/recovery",
        ):
            self.assertTrue((_BR / "rootfs" / Path(sub) / ".setuphelfer_rescue_artifact_placeholder").is_file())

    def test_backend_manifest_detects_routes(self) -> None:
        r = build_rescue_backend_artifacts(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_artifact_backend_status"), "ok")
        checks = (r.get("rescue_artifact_backend") or {}).get("checks") or {}
        self.assertTrue(checks.get("recovery_routes"))

    def test_frontend_manifest_sane(self) -> None:
        build_offline_frontend_artifacts(explicit_overwrite=True)
        data = json.loads((_BR / "frontend_manifest.json").read_text(encoding="utf-8"))
        self.assertTrue(data.get("no_frontend_build_executed"))
        self.assertTrue(data.get("no_pi_installer_assets"))
        for rel in data.get("offline_ready_asset_list") or []:
            rl = str(rel).lower()
            self.assertNotIn("pi-installer", rl)
            self.assertNotIn("pi_installer", rl)

    def test_no_iso_img_created(self) -> None:
        self._run_all_artifacts()
        for fp in _BR.rglob("*"):
            if fp.is_file() and fp.suffix.lower() in (".iso", ".img"):
                self.fail(f"unexpected image artifact: {fp}")

    def test_build_only_under_build_rescue(self) -> None:
        self._run_all_artifacts()
        for fp in _BR.rglob("*"):
            if fp.is_file() or fp.is_dir():
                fp.resolve().relative_to(_BR.resolve())

    def test_overlay_readonly_lower(self) -> None:
        r = build_rescue_overlay_persistence_strategy(explicit_overwrite=True)
        body = r.get("rescue_artifact_overlay_strategy") or {}
        self.assertIn("readonly_lowerdir", body)
        self.assertTrue(body.get("never_auto_target_disk_persistence"))

    def test_branding_blocked_readiness_blocked(self) -> None:
        self._run_all_artifacts()
        (_H / "setuphelfer_branding_guard_check.json").write_text(
            json.dumps({"branding_guard_status": "blocked"}),
            encoding="utf-8",
        )
        (_H / "rescue_iso_final_readiness_gate.json").write_text(json.dumps({"gate_status": "ready"}), encoding="utf-8")
        g = build_rescue_artifact_readiness_gate(explicit_overwrite=True)
        self.assertEqual(g.get("rescue_artifact_readiness_gate_status"), "blocked")

    def test_readiness_ready_when_clean(self) -> None:
        self._run_all_artifacts()
        (_H / "setuphelfer_branding_guard_check.json").write_text(
            json.dumps({"branding_guard_status": "ok"}),
            encoding="utf-8",
        )
        (_H / "rescue_iso_final_readiness_gate.json").write_text(json.dumps({"gate_status": "ready"}), encoding="utf-8")
        g = build_rescue_artifact_readiness_gate(explicit_overwrite=True)
        self.assertEqual(g.get("rescue_artifact_readiness_gate_status"), "ready")

    def test_artifact_runner_no_subprocess(self) -> None:
        raw = _ART_RUNNER.read_text(encoding="utf-8")
        self.assertNotIn("subprocess", raw)
        self.assertNotIn("os.system", raw)

    def test_routes_have_artifact_endpoints(self) -> None:
        txt = _ROUTES.read_text(encoding="utf-8")
        for n in (
            "/rescue/artifact/rootfs",
            "/rescue/artifact/frontend",
            "/rescue/artifact/backend",
            "/rescue/artifact/boot-structure",
            "/rescue/artifact/overlay-strategy",
            "/rescue/artifact/readiness-gate",
        ):
            self.assertIn(n, txt)

    def test_routes_no_forbidden_tooling_strings(self) -> None:
        low = _ROUTES.read_text(encoding="utf-8").lower()
        for bad in ("grub-mkrescue", "xorriso", "dd if=", "mkfs"):
            self.assertNotIn(bad, low)
