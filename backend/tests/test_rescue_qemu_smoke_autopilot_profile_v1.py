"""Tests for Rescue Developer QEMU smoke autopilot profile artifacts."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
QEMU_PROFILE = _REPO / "build/rescue/profiles/developer-qemu"
PUBLIC_PROFILE = _REPO / "build/rescue/profiles/public"
WRAPPER = _REPO / "scripts/rescue-live/run-qemu-developer-iso-smoke.sh"
AUTOPILOT_SH = QEMU_PROFILE / "includes.chroot/usr/local/sbin/setuphelfer-qemu-smoke-autopilot.sh"
AUTOPILOT_SVC = QEMU_PROFILE / "includes.chroot/etc/systemd/system/setuphelfer-qemu-smoke-autopilot.service"
KEYBOARD = QEMU_PROFILE / "includes.chroot/etc/default/keyboard"
XSESSION = QEMU_PROFILE / "includes.chroot/etc/X11/Xsession.d/99-setuphelfer-keyboard-de"
ENABLE_HOOK = QEMU_PROFILE / "hooks/normal/090-enable-qemu-smoke-autopilot.hook.chroot"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class RescueQemuSmokeAutopilotProfileTests(unittest.TestCase):
    def test_autopilot_service_in_developer_qemu_only(self) -> None:
        self.assertTrue(AUTOPILOT_SVC.is_file())
        self.assertIn("setuphelfer-qemu-smoke-autopilot", _read(AUTOPILOT_SVC))
        pub_root = _read(PUBLIC_PROFILE / "manifest.json")
        self.assertNotIn("qemu-smoke-autopilot", pub_root)

    def test_autopilot_script_module_path_and_url(self) -> None:
        text = _read(AUTOPILOT_SH)
        self.assertIn("PYTHONPATH=/opt/setuphelfer-rescue", text)
        self.assertIn("backend.devserver_agent.cli", text)
        self.assertIn("http://10.0.2.2:8001", text)
        self.assertIn("SETUPHELFER_QEMU_SMOKE_RESULT_JSON_BEGIN", text)

    def test_autopilot_script_no_dangerous_commands(self) -> None:
        text = _read(AUTOPILOT_SH).lower()
        for bad in (" dd ", "mkfs", " mount ", " umount ", "apt-get", "apt install"):
            self.assertNotIn(bad, text, msg=bad)
        self.assertNotIn("backup_started\": true", text.replace(" ", ""))

    def test_keyboard_de_in_profile(self) -> None:
        self.assertIn('XKBLAYOUT="de"', _read(KEYBOARD))
        self.assertIn("setxkbmap", _read(XSESSION))
        self.assertIn("-layout de", _read(XSESSION))

    def test_enable_hook_enables_autopilot(self) -> None:
        self.assertIn("setuphelfer-qemu-smoke-autopilot.service", _read(ENABLE_HOOK))

    def test_wrapper_autopilot_options_and_proxy(self) -> None:
        text = _read(WRAPPER)
        self.assertIn("--autopilot", text)
        self.assertIn("--timeout-seconds", text)
        self.assertIn("--proxy-port", text)
        self.assertIn("start-qemu-lab-dev-server-proxy.sh", text)
        self.assertIn("parse-qemu-serial-smoke-result.py", text)
        self.assertNotIn("/qemu_gtk_pid.txt", text.replace("${EVDIR}/qemu_gtk_pid.txt", ""))

    def test_wrapper_vnc_local_only(self) -> None:
        text = _read(WRAPPER)
        self.assertIn("127.0.0.1:1", text)
        self.assertNotIn("0.0.0.0:1", text)

    def test_prepare_script_copies_profile_and_serial_console(self) -> None:
        prep = _read(_REPO / "scripts/rescue-live/prepare-controlled-live-build-tree.sh")
        self.assertIn("copy_profile_overlay", prep)
        self.assertIn("console=ttyS0", prep)
        self.assertIn('write_dev_agent_enable_hook false', prep)

    def test_public_profile_auto_upload_disabled(self) -> None:
        env = _read(PUBLIC_PROFILE / "environment/setuphelfer-dev-agent.env")
        self.assertNotIn("AUTO_UPLOAD=true", env)

    def test_manifest_server_url_8001(self) -> None:
        manifest = json.loads(_read(QEMU_PROFILE / "manifest.json"))
        self.assertIn("8001", manifest.get("server_url", ""))


if __name__ == "__main__":
    unittest.main()
