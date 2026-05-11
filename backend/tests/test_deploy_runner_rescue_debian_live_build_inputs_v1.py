from __future__ import annotations

import json
import shutil
import stat
import unittest
from pathlib import Path

from deploy.runner_rescue_debian_live_build_inputs import (
    build_debian_live_bootloader_templates,
    build_debian_live_build_inputs_final_gate,
    build_debian_live_config_structure,
    build_debian_live_hook_templates,
    build_debian_live_includes_ch_root,
    build_debian_live_package_lists,
    validate_debian_live_build_inputs_safety,
)

_REPO = Path(__file__).resolve().parents[2]
_DL = _REPO / "build" / "rescue" / "debian-live"
_DL_BAK = _REPO / "build" / "rescue" / "debian-live.__test_bak__"
_H = _REPO / "docs" / "evidence" / "runtime-results" / "handoff"
_RUNNER = _REPO / "backend" / "deploy" / "runner_rescue_debian_live_build_inputs.py"
_ROUTES = _REPO / "backend" / "deploy" / "routes.py"

_HANDOFFS = (
    _H / "debian_live_build_inputs_safety.json",
    _H / "debian_live_build_inputs_final_gate.json",
    _H / "rescue_runtime_bundle_consistency_check.json",
    _H / "setuphelfer_branding_guard_check.json",
    _H / "runtime_identifier_zero_state_verification.json",
)


class DeployRunnerRescueDebianLiveBuildInputsV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _H.mkdir(parents=True, exist_ok=True)
        self._hand_bak: dict[Path, bytes | None] = {p: (p.read_bytes() if p.exists() else None) for p in _HANDOFFS}
        for p in _HANDOFFS:
            p.unlink(missing_ok=True)

        self._had_dl = _DL.is_dir()
        if self._had_dl:
            if _DL_BAK.is_dir():
                shutil.rmtree(_DL_BAK)
            _DL.rename(_DL_BAK)

    def tearDown(self) -> None:
        if _DL.is_dir():
            shutil.rmtree(_DL, ignore_errors=True)
        if self._had_dl and _DL_BAK.is_dir():
            if _DL.exists():
                shutil.rmtree(_DL, ignore_errors=True)
            _DL_BAK.rename(_DL)

        for p, bak in self._hand_bak.items():
            if bak is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(bak)

    def _run_all_input_builders(self) -> None:
        build_debian_live_config_structure(explicit_overwrite=True)
        build_debian_live_package_lists(explicit_overwrite=True)
        build_debian_live_includes_ch_root(explicit_overwrite=True)
        build_debian_live_bootloader_templates(explicit_overwrite=True)
        build_debian_live_hook_templates(explicit_overwrite=True)

    def _seed_gate_handoffs_ok(self) -> None:
        (_H / "rescue_runtime_bundle_consistency_check.json").write_text(
            json.dumps({"consistency_status": "ok"}),
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

    def test_config_structure_complete(self) -> None:
        r = build_debian_live_config_structure(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_debian_live_config_structure_status"), "ok")
        for sub in (
            "config/package-lists",
            "config/includes.chroot",
            "config/includes.binary",
            "config/bootloaders/grub-pc",
            "config/bootloaders/grub-efi",
            "config/hooks",
            "manifests",
        ):
            self.assertTrue((_DL / sub).is_dir(), sub)
        mf = _DL / "config_structure_manifest.json"
        self.assertTrue(mf.is_file())

    def test_package_list_required_packages(self) -> None:
        build_debian_live_config_structure(explicit_overwrite=True)
        r = build_debian_live_package_lists(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_debian_live_package_lists_status"), "ok")
        raw = (_DL / "config" / "package-lists" / "setuphelfer-rescue.list.chroot").read_text(encoding="utf-8").lower()
        for p in (
            "python3",
            "python3-venv",
            "python3-pip",
            "nodejs",
            "curl",
            "jq",
            "util-linux",
            "rsync",
            "cryptsetup",
            "dosfstools",
            "e2fsprogs",
            "xfsprogs",
            "btrfs-progs",
            "smartmontools",
            "nvme-cli",
            "network-manager",
            "openssh-client",
            "parted",
            "gdisk",
            "efibootmgr",
            "grub-efi-amd64-bin",
        ):
            self.assertIn(p, raw, p)
        self.assertIn("nginx-light", raw)
        self.assertIn("http.server", raw)

    def test_includes_chroot_layout(self) -> None:
        self._run_all_input_builders()
        for sub in (
            "config/includes.chroot/opt/setuphelfer",
            "config/includes.chroot/etc/setuphelfer",
            "config/includes.chroot/usr/share/setuphelfer/frontend",
        ):
            self.assertTrue((_DL / sub).is_dir())
            ph = _DL / sub / ".setuphelfer_debian_live_include_placeholder"
            self.assertTrue(ph.is_file())

    def test_bootloader_templates_no_auto_restore(self) -> None:
        self._run_all_input_builders()
        menu = (_DL / "config" / "bootloaders" / "grub-pc" / "setuphelfer-grub-menu.cfg.template").read_text(
            encoding="utf-8"
        )
        self.assertIn("No Auto Restore", menu)
        self.assertIn("Operator Confirmation Required", menu)

    def test_hooks_are_template_suffix_non_executable(self) -> None:
        self._run_all_input_builders()
        for name in ("setuphelfer-runtime.hook.chroot.template", "setuphelfer-safety.hook.chroot.template"):
            p = _DL / "config" / "hooks" / name
            self.assertTrue(p.is_file())
            self.assertTrue(name.endswith(".template"))
            mode = p.stat().st_mode
            self.assertEqual(mode & stat.S_IXUSR, 0)

    def test_safety_blocks_apt_systemctl_chroot_dd(self) -> None:
        self._run_all_input_builders()
        bad = _DL / "config" / "package-lists" / "_safety_probe.txt"
        bad.write_text("do not run: apt install x\nsystemctl enable foo\n", encoding="utf-8")
        r = validate_debian_live_build_inputs_safety(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_debian_live_build_inputs_safety_status"), "blocked")
        errs = r.get("errors") or []
        self.assertTrue(any("apt_install" in e for e in errs))
        bad.unlink()

        bad.write_text("example chroot( /mnt/root /bin/bash )\n", encoding="utf-8")
        r2 = validate_debian_live_build_inputs_safety(explicit_overwrite=True)
        self.assertEqual(r2.get("rescue_debian_live_build_inputs_safety_status"), "blocked")
        bad.unlink()

        bad.write_text("disk wipe: dd if=/dev/zero of=/dev/sda\n", encoding="utf-8")
        r3 = validate_debian_live_build_inputs_safety(explicit_overwrite=True)
        self.assertEqual(r3.get("rescue_debian_live_build_inputs_safety_status"), "blocked")
        bad.unlink()

    def test_safety_blocks_iso_img(self) -> None:
        self._run_all_input_builders()
        iso = _DL / "config" / "evil.iso"
        iso.write_bytes(b"x")
        r = validate_debian_live_build_inputs_safety(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_debian_live_build_inputs_safety_status"), "blocked")
        iso.unlink()

    def test_safety_blocks_legacy_identifier(self) -> None:
        self._run_all_input_builders()
        bad = _DL / "config" / "_legacy_probe.txt"
        bad.write_text("forbidden legacy id: pi-installer\n", encoding="utf-8")
        r = validate_debian_live_build_inputs_safety(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_debian_live_build_inputs_safety_status"), "blocked")
        bad.unlink()

    def test_final_gate_ready_when_inputs_and_handoffs_ok(self) -> None:
        self._run_all_input_builders()
        self._seed_gate_handoffs_ok()
        v = validate_debian_live_build_inputs_safety(explicit_overwrite=True)
        self.assertEqual(v.get("rescue_debian_live_build_inputs_safety_status"), "ok")
        g = build_debian_live_build_inputs_final_gate(explicit_overwrite=True)
        self.assertEqual(g.get("rescue_debian_live_build_inputs_final_gate_status"), "ready")

    def test_final_gate_blocked_when_safety_blocked(self) -> None:
        self._run_all_input_builders()
        self._seed_gate_handoffs_ok()
        validate_debian_live_build_inputs_safety(explicit_overwrite=True)
        (_H / "debian_live_build_inputs_safety.json").write_text(
            json.dumps(
                {
                    "debian_live_build_inputs_safety_schema_version": 1,
                    "evaluation": {"debian_live_build_inputs_safety_eval_status": "blocked"},
                }
            ),
            encoding="utf-8",
        )
        g = build_debian_live_build_inputs_final_gate(explicit_overwrite=True)
        self.assertEqual(g.get("rescue_debian_live_build_inputs_final_gate_status"), "blocked")
        self.assertIn("DL_FIN_SAFETY_BLOCKED", g.get("errors") or [])

    def test_runner_no_forbidden_calls(self) -> None:
        raw = _RUNNER.read_text(encoding="utf-8").lower()
        for bad in ("subprocess", "os.system"):
            self.assertNotIn(bad, raw)

    def test_routes_debian_live_input_endpoints(self) -> None:
        txt = _ROUTES.read_text(encoding="utf-8")
        for n in (
            "/rescue/debian-live/config-structure",
            "/rescue/debian-live/package-lists",
            "/rescue/debian-live/includes-chroot",
            "/rescue/debian-live/bootloader-templates",
            "/rescue/debian-live/hook-templates",
            "/rescue/debian-live/input-safety",
            "/rescue/debian-live/final-gate",
        ):
            self.assertIn(n, txt)

    def test_routes_no_forbidden_segments(self) -> None:
        low = _ROUTES.read_text(encoding="utf-8").lower()
        for bad in (
            "/rescue/debian-live/build",
            "/rescue/debian-live/execute",
            "/rescue/debian-live/chroot",
            "/rescue/debian-live/release",
            "/rescue/debian-live/publish",
            "publish-release",
        ):
            self.assertNotIn(bad, low)
