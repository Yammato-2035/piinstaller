"""Tests für devserver_agent.rescue_profile."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from devserver_agent.rescue_profile import (
    build_developer_profile_manifest,
    validate_developer_profile,
    validate_public_profile_guard,
)


def _write_developer_profile(root: Path) -> None:
    (root / "environment").mkdir(parents=True)
    (root / "systemd").mkdir(parents=True)
    (root / "environment" / "setuphelfer-dev-agent.env").write_text(
        "SETUPHELFER_DEV_AGENT_ENABLED=true\n"
        "SETUPHELFER_DEV_AGENT_MODE=local_lab\n"
        "SETUPHELFER_DEV_AGENT_AUTO_UPLOAD=true\n"
        "SETUPHELFER_DEV_AGENT_SERVER_URL=http://127.0.0.1:8000\n",
        encoding="utf-8",
    )
    (root / "manifest.json").write_text(
        json.dumps({
            "profile_id": "rescue_developer_local_lab",
            "agent_enabled": True,
            "agent_mode": "local_lab",
            "developer_auto_upload": True,
            "write_actions_allowed": False,
            "ssh_allowed": False,
        }),
        encoding="utf-8",
    )
    (root / "systemd" / "setuphelfer-dev-agent.service").write_text(
        "[Service]\n"
        "NoNewPrivileges=true\n"
        "ExecStart=/opt/setuphelfer/.venv/bin/python -m backend.devserver_agent.cli --send --json\n",
        encoding="utf-8",
    )


def _write_public_profile(root: Path) -> None:
    (root / "environment").mkdir(parents=True)
    (root / "environment" / "setuphelfer-dev-agent.env").write_text(
        "SETUPHELFER_DEV_AGENT_ENABLED=false\n"
        "SETUPHELFER_DEV_AGENT_MODE=public_rescue\n"
        "SETUPHELFER_DEV_AGENT_AUTO_UPLOAD=false\n",
        encoding="utf-8",
    )
    (root / "manifest.json").write_text(
        json.dumps({
            "profile_id": "rescue_public",
            "agent_enabled": False,
            "developer_auto_upload": False,
        }),
        encoding="utf-8",
    )


class DevAgentRescueProfileTests(unittest.TestCase):
    def test_developer_profile_validates(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_developer_profile(root)
            result = validate_developer_profile(root)
            self.assertTrue(result["ok"])

    def test_developer_contains_local_lab(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_developer_profile(root)
            result = validate_developer_profile(root)
            self.assertEqual(result["environment"]["SETUPHELFER_DEV_AGENT_MODE"], "local_lab")

    def test_developer_auto_upload_only_in_developer(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_developer_profile(root)
            result = validate_developer_profile(root)
            self.assertEqual(result["environment"]["SETUPHELFER_DEV_AGENT_AUTO_UPLOAD"], "true")

    def test_public_blocks_auto_upload(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_public_profile(root)
            result = validate_public_profile_guard(root)
            self.assertTrue(result["ok"])

    def test_public_url_blocked_in_developer_env(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_developer_profile(root)
            env = root / "environment" / "setuphelfer-dev-agent.env"
            env.write_text(env.read_text() + "SETUPHELFER_DEV_AGENT_SERVER_URL=https://example.com\n", encoding="utf-8")
            result = validate_developer_profile(root)
            self.assertFalse(result["ok"])

    def test_token_in_profile_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_developer_profile(root)
            env = root / "environment" / "setuphelfer-dev-agent.env"
            env.write_text(env.read_text() + "SETUPHELFER_DEV_AGENT_TOKEN=secret\n", encoding="utf-8")
            result = validate_developer_profile(root)
            self.assertFalse(result["ok"])

    def test_ssh_allowed_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_developer_profile(root)
            manifest = json.loads((root / "manifest.json").read_text())
            manifest["ssh_allowed"] = True
            (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            result = validate_developer_profile(root)
            self.assertFalse(result["ok"])

    def test_write_actions_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_developer_profile(root)
            manifest = json.loads((root / "manifest.json").read_text())
            manifest["write_actions_allowed"] = True
            (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            result = validate_developer_profile(root)
            self.assertFalse(result["ok"])

    def test_systemd_no_new_privileges(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_developer_profile(root)
            svc = root / "systemd" / "setuphelfer-dev-agent.service"
            svc.write_text("ExecStart=python -m backend.devserver_agent.cli --send\n", encoding="utf-8")
            result = validate_developer_profile(root)
            self.assertFalse(result["ok"])

    def test_systemd_agent_cli_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_developer_profile(root)
            result = validate_developer_profile(root)
            self.assertTrue(result["ok"])

    def test_dangerous_token_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_developer_profile(root)
            svc = root / "systemd" / "setuphelfer-dev-agent.service"
            svc.write_text(svc.read_text() + "ExecStart=sudo dd if=/dev/zero\n", encoding="utf-8")
            result = validate_developer_profile(root)
            self.assertFalse(result["ok"])

    def test_build_manifest_helper(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_developer_profile(root)
            built = build_developer_profile_manifest(root)
            self.assertTrue(built["systemd_service"])


class DevAgentRescueProfileRepoTests(unittest.TestCase):
    def test_repo_developer_profile_validates(self) -> None:
        repo = Path(__file__).resolve().parent.parent.parent
        dev = repo / "build" / "rescue" / "profiles" / "developer"
        if not dev.is_dir():
            self.skipTest("developer profile not in workspace")
        result = validate_developer_profile(dev)
        self.assertTrue(result["ok"], msg=str(result.get("errors")))

    def test_repo_public_guard(self) -> None:
        repo = Path(__file__).resolve().parent.parent.parent
        pub = repo / "build" / "rescue" / "profiles" / "public"
        result = validate_public_profile_guard(pub)
        self.assertTrue(result["ok"], msg=str(result.get("errors")))


if __name__ == "__main__":
    unittest.main()
