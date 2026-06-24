from __future__ import annotations

import unittest
from pathlib import Path

from deploy.routes_source_aggregate import read_deploy_routes_aggregate

_REPO = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO / "scripts/rescue/build-rescue-iso.sh"
_CONTROLLED = _REPO / "scripts/rescue/build-rescue-iso-controlled.sh"


class DeployRunnerRescueApiRoutesAndScriptV1Tests(unittest.TestCase):
    def test_rescue_post_routes_registered(self) -> None:
        txt = read_deploy_routes_aggregate()
        for needle in (
            "/rescue/live-os-base-decision",
            "/rescue/component-inventory",
            "/rescue/mvp-scope-gate",
            "/rescue/debian-live-build-plan",
            "/rescue/debian-live/config-structure",
            "/rescue/debian-live/package-lists",
            "/rescue/debian-live/includes-chroot",
            "/rescue/debian-live/bootloader-templates",
            "/rescue/debian-live/hook-templates",
            "/rescue/debian-live/input-safety",
            "/rescue/debian-live/final-gate",
            "/rescue/dry-build/stage-graph",
            "/rescue/dry-build/input-resolution",
            "/rescue/dry-build/package-resolution",
            "/rescue/dry-build/build-order-validation",
            "/rescue/dry-build/execution-simulation",
            "/rescue/dry-build/final-gate",
            "/rescue/dry-build/safety-validation",
            "/rescue/build-sandbox/root",
            "/rescue/build-sandbox/config-copy-plan",
            "/rescue/build-sandbox/runtime-copy-plan",
            "/rescue/build-sandbox/overlay-workspace-plan",
            "/rescue/build-sandbox/cleanup-plan",
            "/rescue/build-sandbox/safety-validation",
            "/rescue/build-sandbox/final-gate",
            "/rescue/iso-test-matrix",
            "/rescue/build-readiness-gate",
            "/rescue/live-build-config",
            "/rescue/iso-execution-plan",
            "/rescue/iso-build-precheck",
            "/rescue/iso-build-execute",
            "/rescue/vm-test-plan",
            "/rescue/vm-test-execute",
            "/rescue/iso-live-runtime-probe",
            "/rescue/iso-readiness-gate",
            "/rescue/storage-discovery",
            "/rescue/readonly-mount-validation",
            "/rescue/efi-boot-analysis",
            "/rescue/evidence-export",
            "/rescue/remote-help-preparation",
            "/rescue/live-hardware-matrix",
            "/rescue/live-runtime-safety-gate",
            "/rescue/recovery-scenario-matrix",
            "/rescue/recovery-target-validation",
            "/rescue/backup-discovery-verify",
            "/rescue/restore-preview",
            "/rescue/hardware-recovery-test-chain",
            "/rescue/final-recovery-readiness-gate",
            "/rescue/manual-recovery-operator-guides",
            "/rescue/recovery-evidence-timeline",
            "/rescue/iso-baseline",
            "/rescue/iso-filesystem-layout",
            "/rescue/offline-runtime-validation",
            "/rescue/bootflow-simulation",
            "/rescue/iso-safety-validation",
            "/rescue/iso-final-readiness-gate",
            "/rescue/iso-build-plan",
        ):
            self.assertIn(needle, txt)

    def test_no_forbidden_rescue_route_segments(self) -> None:
        low = read_deploy_routes_aggregate().lower()
        for bad in (
            "write-usb",
            "restore-execute",
            "repair-bootloader",
            "install-system",
            "deploy-release",
            "publish-release",
            "partition-write",
            "usb-write",
            "grub-repair",
            "efi-repair",
            "auto-repair",
            "efi-write",
            "auto-build",
            "auto-write",
        ):
            self.assertNotIn(bad, low)

    def test_build_script_no_destructive_commands(self) -> None:
        raw = _SCRIPT.read_text(encoding="utf-8")
        for ln in raw.splitlines():
            s = ln.strip()
            if not s or s.startswith("#"):
                continue
            self.assertFalse(s.startswith("dd "), s)
            self.assertFalse(s.startswith("mkfs"), s)
            self.assertFalse(s.startswith("systemctl"), s)
        self.assertIn("set -euo pipefail", raw)
        self.assertNotIn("dd if=", raw)
        self.assertNotIn("dd of=", raw)

    def test_controlled_build_script_safety(self) -> None:
        raw = _CONTROLLED.read_text(encoding="utf-8")
        self.assertIn("set -euo pipefail", raw)
        self.assertIn("build/rescue", raw)
        self.assertIn("/output", raw)
        for ln in raw.splitlines():
            s = ln.strip()
            if not s or s.startswith("#"):
                continue
            self.assertFalse(s.startswith("dd "), s)
            self.assertFalse(s.startswith("mkfs"), s)
            self.assertFalse(s.startswith("wipefs"), s)
            self.assertFalse(s.startswith("systemctl"), s)
        self.assertNotIn("mount /dev/sd", raw)
