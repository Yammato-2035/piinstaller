"""Tests für devserver_agent.rescue_iso_dry_build — kein echter ISO-Build."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from devserver_agent.rescue_iso_dry_build import (
    build_agent_profile_placement_plan,
    build_rescue_developer_iso_dry_build_manifest,
    validate_no_real_build_artifacts,
    validate_rescue_developer_iso_dry_build,
)
from tests.test_devserver_agent_rescue_profile_v1 import (
    _write_developer_profile,
    _write_public_profile,
)

_REPO = Path(__file__).resolve().parent.parent.parent
_DRY_BUILD_MODULE = _REPO / "backend" / "devserver_agent" / "rescue_iso_dry_build.py"
_CLI_MODULE = _REPO / "backend" / "devserver_agent" / "cli.py"


class RescueIsoDryBuildTests(unittest.TestCase):
    def test_dry_build_manifest_created(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            dev = Path(td) / "developer"
            pub = Path(td) / "public"
            out = Path(td) / "manifest.json"
            _write_developer_profile(dev)
            _write_public_profile(pub)
            manifest = build_rescue_developer_iso_dry_build_manifest(str(dev), str(pub), str(out))
            self.assertTrue(out.is_file())
            self.assertIn("status", manifest)

    def test_real_iso_build_false(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            dev = Path(td) / "developer"
            pub = Path(td) / "public"
            out = Path(td) / "manifest.json"
            _write_developer_profile(dev)
            _write_public_profile(pub)
            manifest = build_rescue_developer_iso_dry_build_manifest(str(dev), str(pub), str(out))
            self.assertFalse(manifest["real_iso_build"])
            self.assertFalse(manifest["generated_iso"])
            self.assertTrue(manifest["dry_build"])

    def test_developer_agent_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            dev = Path(td) / "developer"
            pub = Path(td) / "public"
            out = Path(td) / "manifest.json"
            _write_developer_profile(dev)
            _write_public_profile(pub)
            manifest = build_rescue_developer_iso_dry_build_manifest(str(dev), str(pub), str(out))
            self.assertTrue(manifest["developer_profile"]["agent_enabled"])

    def test_public_agent_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            dev = Path(td) / "developer"
            pub = Path(td) / "public"
            out = Path(td) / "manifest.json"
            _write_developer_profile(dev)
            _write_public_profile(pub)
            manifest = build_rescue_developer_iso_dry_build_manifest(str(dev), str(pub), str(out))
            self.assertFalse(manifest["public_profile_guard"]["agent_enabled"])

    def test_public_auto_upload_false(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            dev = Path(td) / "developer"
            pub = Path(td) / "public"
            out = Path(td) / "manifest.json"
            _write_developer_profile(dev)
            _write_public_profile(pub)
            manifest = build_rescue_developer_iso_dry_build_manifest(str(dev), str(pub), str(out))
            self.assertFalse(manifest["public_profile_guard"]["auto_upload"])

    def test_ssh_false(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            dev = Path(td) / "developer"
            pub = Path(td) / "public"
            out = Path(td) / "manifest.json"
            _write_developer_profile(dev)
            _write_public_profile(pub)
            manifest = build_rescue_developer_iso_dry_build_manifest(str(dev), str(pub), str(out))
            self.assertFalse(manifest["developer_profile"]["ssh_allowed"])

    def test_write_actions_false(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            dev = Path(td) / "developer"
            pub = Path(td) / "public"
            out = Path(td) / "manifest.json"
            _write_developer_profile(dev)
            _write_public_profile(pub)
            manifest = build_rescue_developer_iso_dry_build_manifest(str(dev), str(pub), str(out))
            self.assertFalse(manifest["developer_profile"]["write_actions_allowed"])

    def test_public_url_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            dev = Path(td) / "developer"
            pub = Path(td) / "public"
            out = Path(td) / "manifest.json"
            _write_developer_profile(dev)
            _write_public_profile(pub)
            env = dev / "environment" / "setuphelfer-dev-agent.env"
            env.write_text(
                env.read_text(encoding="utf-8") + "SETUPHELFER_DEV_AGENT_SERVER_URL=https://example.com\n",
                encoding="utf-8",
            )
            manifest = build_rescue_developer_iso_dry_build_manifest(str(dev), str(pub), str(out))
            self.assertEqual(manifest["status"], "blocked")

    def test_token_secret_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            dev = Path(td) / "developer"
            pub = Path(td) / "public"
            out = Path(td) / "manifest.json"
            _write_developer_profile(dev)
            _write_public_profile(pub)
            env = dev / "environment" / "setuphelfer-dev-agent.env"
            env.write_text(
                env.read_text(encoding="utf-8") + "SETUPHELFER_DEV_AGENT_TOKEN=secret\n",
                encoding="utf-8",
            )
            manifest = build_rescue_developer_iso_dry_build_manifest(str(dev), str(pub), str(out))
            self.assertEqual(manifest["status"], "blocked")

    def test_forbidden_artifact_detected_in_output_dir(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "evil.iso").write_text("fake", encoding="utf-8")
            scan = validate_no_real_build_artifacts(root)
            self.assertFalse(scan["ok"])

    def test_placement_plan(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            dev = Path(td)
            _write_developer_profile(dev)
            plan = build_agent_profile_placement_plan(dev)
            self.assertEqual(plan["runtime_module_required"], "backend.devserver_agent")
            self.assertIn("/etc/setuphelfer", plan["environment_target"])

    def test_cli_rescue_iso_dry_build_json(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            dev = Path(td) / "developer"
            pub = Path(td) / "public"
            out = Path(td) / "manifest.json"
            _write_developer_profile(dev)
            _write_public_profile(pub)
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "backend.devserver_agent.cli",
                    "--rescue-iso-dry-build",
                    "--developer-profile-root",
                    str(dev),
                    "--public-profile-root",
                    str(pub),
                    "--output",
                    str(out),
                    "--json",
                ],
                cwd=str(_REPO),
                env={**os.environ, "PYTHONPATH": f"{_REPO}/backend:{_REPO}"},
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertIn(proc.returncode, (0, 10), msg=proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["code"], "RESCUE_DEVELOPER_ISO_DRY_BUILD")
            self.assertFalse(payload["real_iso_build"])
            self.assertIn(payload["status"], ("ok", "review_required"))

    def test_no_build_commands_in_dry_build_module(self) -> None:
        text = _DRY_BUILD_MODULE.read_text(encoding="utf-8")
        for pattern in ("subprocess", "os.system", "os.popen", "Popen("):
            self.assertNotIn(pattern, text)

    def test_no_build_commands_in_cli_dry_build_path(self) -> None:
        text = _CLI_MODULE.read_text(encoding="utf-8")
        self.assertIn("rescue_iso_dry_build", text)
        for token in ("subprocess", "os.system", "lb build", "debootstrap"):
            self.assertNotIn(token, text.split("cmd_rescue_iso_dry_build")[1][:800])


class RescueIsoDryBuildRepoTests(unittest.TestCase):
    def test_repo_dry_build_manifest_ok(self) -> None:
        dev = _REPO / "build" / "rescue" / "profiles" / "developer"
        pub = _REPO / "build" / "rescue" / "profiles" / "public"
        if not dev.is_dir():
            self.skipTest("developer profile missing")
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "manifest.json"
            manifest = build_rescue_developer_iso_dry_build_manifest(str(dev), str(pub), str(out))
            self.assertIn(manifest["status"], ("ok", "review_required"))
            validation = validate_rescue_developer_iso_dry_build(manifest)
            self.assertIn(validation["status"], ("ok", "review_required"))


if __name__ == "__main__":
    unittest.main()
