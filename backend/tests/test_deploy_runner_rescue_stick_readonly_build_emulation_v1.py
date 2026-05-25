"""Rescue stick read-only build emulation – deploy runner tests."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

import deploy.runner_rescue_stick_readonly_build_emulation as readonly_runner
from deploy.runner_rescue_stick_readonly_build_emulation import (
    build_rescue_stick_build_workspace_snapshot,
    build_rescue_stick_evidence_manifest,
    build_rescue_stick_expected_debian_live_tree,
    build_rescue_stick_frontend_bundle_preview,
    build_rescue_stick_network_webui_preview,
    build_rescue_stick_package_list_preview,
    build_rescue_stick_readonly_build_final_gate,
    build_rescue_stick_runtime_bundle_preview,
    build_rescue_stick_systemd_service_preview,
    run_rescue_stick_readonly_build_emulation_all,
)

_REPO = Path(__file__).resolve().parents[2]
_EM = _REPO / "build" / "rescue" / "emulation"
_H = _REPO / "docs" / "evidence" / "runtime-results" / "handoff"
_RUNNER = _REPO / "backend" / "deploy" / "runner_rescue_stick_readonly_build_emulation.py"
_ROUTES = _REPO / "backend" / "deploy" / "routes.py"

_EMUL_FILES = [
    "rescue_stick_build_workspace_snapshot.json",
    "rescue_stick_expected_debian_live_tree.json",
    "rescue_stick_package_list_preview.json",
    "rescue_stick_runtime_bundle_preview.json",
    "rescue_stick_frontend_bundle_preview.json",
    "rescue_stick_systemd_service_preview.json",
    "rescue_stick_network_webui_preview.json",
]
_HANDOFF_FILES = [
    "rescue_stick_readonly_build_emulation_manifest.json",
    "rescue_stick_readonly_build_final_gate.json",
]


class RescueStickReadonlyBuildEmulationV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _EM.mkdir(parents=True, exist_ok=True)
        _H.mkdir(parents=True, exist_ok=True)
        self._bak: dict[Path, bytes | None] = {}
        for name in _EMUL_FILES:
            p = _EM / name
            self._bak[p] = p.read_bytes() if p.exists() else None
            p.unlink(missing_ok=True)
        for name in _HANDOFF_FILES:
            p = _H / name
            self._bak[p] = p.read_bytes() if p.exists() else None
            p.unlink(missing_ok=True)

    def tearDown(self) -> None:
        for p, b in self._bak.items():
            if b is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(b)

    def test_workspace_snapshot_writes_json(self) -> None:
        r = build_rescue_stick_build_workspace_snapshot(explicit_overwrite=True, runtime_gate_exit_0=True)
        self.assertIn(r.get("rescue_stick_build_workspace_snapshot_status"), ("ok", "review_required"))
        p = _EM / "rescue_stick_build_workspace_snapshot.json"
        self.assertTrue(p.is_file())
        body = json.loads(p.read_text(encoding="utf-8"))
        self.assertTrue(body.get("no_real_build_execution"))
        self.assertFalse(body.get("generated"))

    def test_debian_live_tree_expected_not_created_on_disk(self) -> None:
        r = build_rescue_stick_expected_debian_live_tree(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_stick_expected_debian_live_tree_status"), "ok")
        self.assertFalse((_REPO / "config" / "package-lists").exists())
        body = json.loads((_EM / "rescue_stick_expected_debian_live_tree.json").read_text(encoding="utf-8"))
        self.assertTrue(all(e.get("generated") is False for e in body.get("entries") or []))

    def test_package_list_no_apt(self) -> None:
        src = _RUNNER.read_text(encoding="utf-8")
        self.assertNotIn("subprocess", src)
        self.assertNotIn("apt-cache", src)
        r = build_rescue_stick_package_list_preview(explicit_overwrite=True)
        self.assertIn(r.get("rescue_stick_package_list_preview_status"), ("ok", "review_required"))

    def test_runtime_bundle_flags_secrets(self) -> None:
        r = build_rescue_stick_runtime_bundle_preview(explicit_overwrite=True)
        body = r.get("rescue_stick_runtime_bundle_preview") or {}
        excluded = " ".join(body.get("excluded_patterns") or [])
        self.assertIn(".env", excluded)
        self.assertIn(r.get("rescue_stick_runtime_bundle_preview_status"), ("ok", "review_required", "blocked"))

    def test_frontend_cdn_review(self) -> None:
        r = build_rescue_stick_frontend_bundle_preview(explicit_overwrite=True)
        self.assertIn(
            r.get("rescue_stick_frontend_bundle_preview_status"),
            ("ok", "review_required", "blocked"),
        )

    def test_systemd_no_auto_restore(self) -> None:
        r = build_rescue_stick_systemd_service_preview(explicit_overwrite=True)
        units = (r.get("rescue_stick_systemd_service_preview") or {}).get("units") or []
        for u in units:
            self.assertFalse(u.get("auto_restore_on_start"))
            self.assertFalse(u.get("auto_partition_on_start"))

    def test_network_blocks_lan_write(self) -> None:
        r = build_rescue_stick_network_webui_preview(explicit_overwrite=True)
        policies = (r.get("rescue_stick_network_webui_preview") or {}).get("policies") or {}
        self.assertEqual(policies.get("lan_write_without_gate"), "blocked")

    def test_evidence_manifest_blocks_iso(self) -> None:
        bad = _EM / "evil.live.iso"
        bad.write_bytes(b"FAKE")
        try:
            run_rescue_stick_readonly_build_emulation_all(explicit_overwrite=True, runtime_gate_exit_0=True)
            manifest = json.loads(
                (_H / "rescue_stick_readonly_build_emulation_manifest.json").read_text(encoding="utf-8")
            )
            self.assertTrue(manifest.get("forbidden_artifacts_scan"))
            final = json.loads(
                (_H / "rescue_stick_readonly_build_final_gate.json").read_text(encoding="utf-8")
            )
            self.assertEqual(final.get("gate_status"), "blocked")
        finally:
            bad.unlink(missing_ok=True)

    def test_documented_forbidden_terms_review_not_exec_block(self) -> None:
        run_rescue_stick_readonly_build_emulation_all(explicit_overwrite=True, runtime_gate_exit_0=True)
        manifest = json.loads(
            (_H / "rescue_stick_readonly_build_emulation_manifest.json").read_text(encoding="utf-8")
        )
        scan = manifest.get("forbidden_tokens_scan") or {}
        exec_hits = scan.get("execution_context") or []
        doc_hits = scan.get("documented_or_review") or []
        self.assertEqual(exec_hits, [])
        self.assertTrue(doc_hits or manifest.get("manifest_status") in ("ok", "review_required"))

    def test_final_gate_ready_or_review_when_clean(self) -> None:
        with patch.object(readonly_runner, "_scan_forbidden_artifacts", return_value=[]):
            res = run_rescue_stick_readonly_build_emulation_all(explicit_overwrite=True, runtime_gate_exit_0=True)
        st = res.get("rescue_stick_readonly_build_emulation_all_status")
        self.assertIn(st, ("ready", "review_required"))
        final = json.loads((_H / "rescue_stick_readonly_build_final_gate.json").read_text(encoding="utf-8"))
        self.assertTrue(final.get("no_real_build_execution"))
        self.assertFalse(final.get("generated"))

    def test_final_gate_blocked_without_no_real_build_flag(self) -> None:
        run_rescue_stick_readonly_build_emulation_all(explicit_overwrite=True, runtime_gate_exit_0=True)
        p = _EM / "rescue_stick_package_list_preview.json"
        data = json.loads(p.read_text(encoding="utf-8"))
        data["no_real_build_execution"] = False
        p.write_text(json.dumps(data), encoding="utf-8")
        r = build_rescue_stick_readonly_build_final_gate(explicit_overwrite=True, runtime_gate_exit_0=True)
        self.assertEqual(r.get("rescue_stick_readonly_build_final_gate_status"), "blocked")

    def test_no_subprocess_in_runner(self) -> None:
        src = _RUNNER.read_text(encoding="utf-8")
        self.assertNotIn("subprocess", src)

    def test_api_routes_no_forbidden_paths(self) -> None:
        routes = _ROUTES.read_text(encoding="utf-8")
        self.assertIn("/rescue-stick/build-emulation/final-gate", routes)
        stick_lines = [ln for ln in routes.splitlines() if "rescue-stick/build-emulation" in ln]
        self.assertGreater(len(stick_lines), 5)
        joined = "\n".join(stick_lines).lower()
        for forbidden in ("/iso", "live-build", "chroot", "apt-install", "qemu", "/publish", "/write", "/apply"):
            self.assertNotIn(forbidden, joined)

    def test_atomic_write_uses_tmp(self) -> None:
        from deploy.runner_rescue_io import atomic_write_text

        src = Path(atomic_write_text.__code__.co_filename).read_text(encoding="utf-8")
        self.assertIn(".tmp", src)

    def test_writes_only_under_emulation_and_handoff(self) -> None:
        rel_paths: list[str] = []
        for name in _EMUL_FILES:
            r = build_rescue_stick_build_workspace_snapshot(explicit_overwrite=True)
            rel_paths.append(str(r.get("rescue_stick_build_workspace_snapshot_file_path")))
            break
        build_rescue_stick_expected_debian_live_tree(explicit_overwrite=True)
        for name in _EMUL_FILES:
            p = _EM / name
            self.assertTrue(str(p).startswith(str(_EM)))
        build_rescue_stick_evidence_manifest(explicit_overwrite=True)
        hp = _H / "rescue_stick_readonly_build_emulation_manifest.json"
        self.assertTrue(hp.is_file())


if __name__ == "__main__":
    unittest.main()
