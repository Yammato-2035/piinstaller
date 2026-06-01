"""Rescue runtime module path and QEMU profile contract tests."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]

FORBIDDEN_RESCUE_CLI = re.compile(
    r"PYTHONPATH=/opt/setuphelfer-rescue/backend[^\n]*\n[^\n]*"
    r"python3\s+-m\s+devserver_agent\.cli",
    re.MULTILINE,
)
WRONG_EXEC = re.compile(r"ExecStart=.*\s-m\s+devserver_agent\.cli\b")
CORRECT_EXEC = re.compile(r"ExecStart=.*\s-m\s+backend\.devserver_agent\.cli\b")
CORRECT_PYTHONPATH = "PYTHONPATH=/opt/setuphelfer-rescue"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class RescueRuntimeModulePathTests(unittest.TestCase):
    def test_prepare_script_uses_backend_module(self) -> None:
        text = _read(_REPO / "scripts/rescue-live/prepare-controlled-live-build-tree.sh")
        self.assertIn("backend.devserver_agent.cli", text)
        self.assertIn(CORRECT_PYTHONPATH, text)
        self.assertNotRegex(text, r"-m devserver_agent\.cli")

    def test_developer_qemu_profile_systemd(self) -> None:
        svc = _REPO / "build/rescue/profiles/developer-qemu/systemd/setuphelfer-dev-agent.service"
        text = _read(svc)
        self.assertRegex(text, CORRECT_EXEC)
        self.assertIn(CORRECT_PYTHONPATH, text)
        self.assertNotRegex(text, WRONG_EXEC)

    def test_developer_qemu_env_host_url(self) -> None:
        env = _read(
            _REPO / "build/rescue/profiles/developer-qemu/environment/setuphelfer-dev-agent.env"
        )
        self.assertIn("SETUPHELFER_DEV_AGENT_SERVER_URL=http://10.0.2.2:8001", env)
        self.assertIn("SETUPHELFER_DEV_AGENT_MODE=local_lab", env)
        self.assertNotIn("public_rescue", env)

    def test_developer_qemu_manifest_no_public_exposure(self) -> None:
        manifest = json.loads(
            _read(_REPO / "build/rescue/profiles/developer-qemu/manifest.json")
        )
        self.assertTrue(manifest.get("qemu_host_fallback"))
        self.assertEqual(manifest.get("server_url"), "http://10.0.2.2:8001")
        self.assertFalse(manifest.get("public_auto_upload", True))
        remote = manifest.get("qemu", {}).get("remote_console", {})
        self.assertEqual(remote.get("bind"), "127.0.0.1")
        self.assertFalse(remote.get("public_exposure", True))

    def test_qemu_runbook_examples_use_backend_module(self) -> None:
        for name in (
            "docs/runbooks/RESCUE_DEVELOPER_ISO_QEMU_BOOT_PLAN_DE.md",
            "docs/runbooks/RESCUE_DEVELOPER_ISO_QEMU_BOOT_PLAN_EN.md",
        ):
            text = _read(_REPO / name)
            self.assertIn("backend.devserver_agent.cli", text)
            self.assertIn("PYTHONPATH=/opt/setuphelfer-rescue", text)

    def test_qemu_wrapper_has_lab_proxy(self) -> None:
        text = _read(_REPO / "scripts/rescue-live/run-qemu-developer-iso-smoke.sh")
        self.assertIn("start-qemu-lab-dev-server-proxy.sh", text)
        self.assertIn("LAB_PROXY_PORT", text)
        proxy = _read(_REPO / "scripts/rescue-live/start-qemu-lab-dev-server-proxy.sh")
        self.assertIn("bind=0.0.0.0", proxy)
        self.assertIn("127.0.0.1:8000", proxy)
        self.assertIn("reusing proxy already listening", proxy)
        self.assertIn("PROXY_BIND", proxy)
        self.assertIn("127.0.0.1", proxy)
        self.assertIn("-enable-kvm", _read(_REPO / "scripts/rescue-live/run-qemu-developer-iso-smoke.sh"))

    def test_public_profile_auto_upload_disabled(self) -> None:
        env = _read(_REPO / "build/rescue/profiles/public/environment/setuphelfer-dev-agent.env")
        self.assertNotIn("SETUPHELFER_DEV_AGENT_AUTO_UPLOAD=true", env)

    def test_no_token_in_qemu_profile(self) -> None:
        env = _read(
            _REPO / "build/rescue/profiles/developer-qemu/environment/setuphelfer-dev-agent.env"
        )
        self.assertNotIn("TOKEN=", env.upper())
        self.assertNotIn("SECRET=", env.upper())


if __name__ == "__main__":
    unittest.main()
