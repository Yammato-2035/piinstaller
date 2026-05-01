"""
Tests fuer LAN-IP-Erkennung und Monitoring-Status.

Lauf:
  cd backend && python -m unittest tests.test_network_and_monitoring_status_v1 -v
"""

import asyncio
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

try:
    import app as app_module  # noqa: E402
    _HAS_APP = True
except Exception:  # pragma: no cover - Umgebung ohne FastAPI etc.
    app_module = None
    _HAS_APP = False


def _cp(cmd, returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(cmd, returncode, stdout, stderr)


@unittest.skipUnless(_HAS_APP, "app/FastAPI nicht verfuegbar")
class TestNetworkInfoDetection(unittest.TestCase):
    @patch("app.subprocess.run")
    @patch("app.run_command")
    def test_normal_lan_ip_from_ip_command(self, mock_run_command, mock_subprocess_run):
        mock_run_command.return_value = {
            "success": True,
            "stdout": "2: enp5s0    inet 192.168.178.140/24 brd 192.168.178.255 scope global enp5s0\n",
        }

        def side_effect(cmd, **kwargs):
            if cmd == ["hostname"]:
                return _cp(cmd, 0, "host-a\n")
            if cmd == ["hostname", "-I"]:
                return _cp(cmd, 0, "")
            raise AssertionError(f"unexpected subprocess cmd: {cmd}")

        mock_subprocess_run.side_effect = side_effect
        info = app_module.get_network_info()
        self.assertEqual(info["ips"], ["192.168.178.140"])
        self.assertEqual(info["primary_ip"], "192.168.178.140")
        self.assertEqual(info["source"], "ip-addr-global")
        self.assertEqual(info["localhost"], "127.0.0.1")
        self.assertEqual(info["warnings"], [])

    @patch("app.subprocess.run")
    @patch("app.run_command")
    def test_only_localhost_results_in_empty_lan_with_warning(self, mock_run_command, mock_subprocess_run):
        mock_run_command.return_value = {"success": True, "stdout": ""}

        def side_effect(cmd, **kwargs):
            if cmd == ["hostname", "-I"]:
                return _cp(cmd, 0, "127.0.0.1 ::1\n")
            if cmd == ["hostname"]:
                return _cp(cmd, 0, "host-b\n")
            raise AssertionError(f"unexpected subprocess cmd: {cmd}")

        mock_subprocess_run.side_effect = side_effect
        info = app_module.get_network_info()
        self.assertEqual(info["ips"], [])
        self.assertIsNone(info["primary_ip"])
        self.assertEqual(info["source"], "none")
        self.assertTrue(any("keine LAN-IP erkannt" in w for w in info["warnings"]))

    @patch("app.subprocess.run")
    @patch("app.run_command")
    def test_docker_veth_and_wg_are_filtered(self, mock_run_command, mock_subprocess_run):
        mock_run_command.return_value = {
            "success": True,
            "stdout": (
                "2: docker0    inet 172.17.0.1/16 brd 172.17.255.255 scope global docker0\n"
                "3: veth1234   inet 172.18.0.1/16 brd 172.18.255.255 scope global veth1234\n"
                "4: wg0        inet 10.8.0.2/24 brd 10.8.0.255 scope global wg0\n"
                "5: enp5s0     inet 192.168.1.42/24 brd 192.168.1.255 scope global enp5s0\n"
            ),
        }

        def side_effect(cmd, **kwargs):
            if cmd == ["hostname"]:
                return _cp(cmd, 0, "host-c\n")
            if cmd == ["hostname", "-I"]:
                return _cp(cmd, 0, "")
            raise AssertionError(f"unexpected subprocess cmd: {cmd}")

        mock_subprocess_run.side_effect = side_effect
        info = app_module.get_network_info()
        self.assertEqual(info["ips"], ["192.168.1.42"])
        self.assertEqual(len(info["interfaces"]), 1)
        self.assertEqual(info["interfaces"][0]["name"], "enp5s0")

    @patch("app.subprocess.run")
    @patch("app.run_command")
    def test_hostname_i_fallback_when_ip_command_empty(self, mock_run_command, mock_subprocess_run):
        mock_run_command.return_value = {"success": False, "stdout": ""}

        def side_effect(cmd, **kwargs):
            if cmd == ["hostname", "-I"]:
                return _cp(cmd, 0, "192.168.55.9 127.0.0.1\n")
            if cmd == ["hostname"]:
                return _cp(cmd, 0, "host-d\n")
            raise AssertionError(f"unexpected subprocess cmd: {cmd}")

        mock_subprocess_run.side_effect = side_effect
        info = app_module.get_network_info()
        self.assertEqual(info["ips"], ["192.168.55.9"])
        self.assertEqual(info["primary_ip"], "192.168.55.9")
        self.assertEqual(info["source"], "hostname-I")


@unittest.skipUnless(_HAS_APP, "app/FastAPI nicht verfuegbar")
class TestMonitoringStatus(unittest.TestCase):
    @patch("app.check_installed")
    @patch("app.run_command")
    def test_grafana_installed_but_stopped(self, mock_run_command, mock_check_installed):
        def check_installed_side_effect(name):
            return name in {"prometheus", "grafana", "node_exporter"}

        def run_command_side_effect(cmd, *args, **kwargs):
            if "systemctl is-active prometheus" in cmd:
                return {"success": True, "stdout": "active"}
            if "systemctl is-active grafana-server" in cmd:
                return {"success": False, "stdout": "inactive"}
            if "systemctl is-active node_exporter" in cmd:
                return {"success": True, "stdout": "active"}
            if ":3000 " in cmd:
                return {"success": False, "stdout": ""}
            if ":9100 " in cmd:
                return {"success": True, "stdout": "LISTEN"}
            if "which " in cmd or "test -f " in cmd or "list-unit-files" in cmd or "list-units --all" in cmd:
                return {"success": True, "stdout": ""}
            return {"success": False, "stdout": "", "stderr": ""}

        mock_check_installed.side_effect = check_installed_side_effect
        mock_run_command.side_effect = run_command_side_effect

        status = asyncio.run(app_module.monitoring_status())
        self.assertTrue(status["grafana"]["installed"])
        self.assertFalse(status["grafana"]["running"])


@unittest.skipUnless(_HAS_APP, "app/FastAPI nicht verfuegbar")
class TestSystemStatusPolicy(unittest.TestCase):
    @patch("app.get_updates_categorized")
    @patch("app.get_security_config")
    def test_all_security_components_green(self, mock_get_security, mock_get_updates):
        mock_get_security.return_value = {
            "ssh": {"config": "PermitRootLogin no\n"},
            "ufw": {"installed": True, "active": True, "status": "active"},
            "fail2ban": {"running": True},
            "auto_updates": {"enabled": True},
            "ssh_hardening": {"enabled": True},
            "audit_logging": {"enabled": True},
        }
        mock_get_updates.return_value = {"total": 0, "categories": {"security": 0, "critical": 0, "necessary": 0, "optional": 0}}
        s = app_module._compute_system_status()
        self.assertEqual(s["security"], "green")

    @patch("app.get_updates_categorized")
    @patch("app.get_security_config")
    def test_missing_one_component_yellow(self, mock_get_security, mock_get_updates):
        mock_get_security.return_value = {
            "ssh": {"config": "PermitRootLogin no\n"},
            "ufw": {"installed": True, "active": True, "status": "active"},
            "fail2ban": {"running": True},
            "auto_updates": {"enabled": False},
            "ssh_hardening": {"enabled": True},
            "audit_logging": {"enabled": True},
        }
        mock_get_updates.return_value = {"total": 0, "categories": {"security": 0, "critical": 0, "necessary": 0, "optional": 0}}
        s = app_module._compute_system_status()
        self.assertEqual(s["security"], "yellow")

    @patch("app.get_updates_categorized")
    @patch("app.get_security_config")
    def test_critical_security_gap_root_login_enabled(self, mock_get_security, mock_get_updates):
        mock_get_security.return_value = {
            "ssh": {"config": "PermitRootLogin yes\n"},
            "ufw": {"installed": True, "active": True, "status": "active"},
            "fail2ban": {"running": True},
            "auto_updates": {"enabled": True},
            "ssh_hardening": {"enabled": False},
            "audit_logging": {"enabled": True},
        }
        mock_get_updates.return_value = {"total": 0, "categories": {"security": 0, "critical": 0, "necessary": 0, "optional": 0}}
        s = app_module._compute_system_status()
        self.assertEqual(s["security"], "red")

    @patch("app.get_updates_categorized")
    @patch("app.get_security_config")
    def test_updates_none_green(self, mock_get_security, mock_get_updates):
        mock_get_security.return_value = {"ufw": {"installed": True, "active": True}, "ssh": {"config": "PermitRootLogin no\n"}}
        mock_get_updates.return_value = {"total": 0, "categories": {"security": 0, "critical": 0, "necessary": 0, "optional": 0}}
        s = app_module._compute_system_status()
        self.assertEqual(s["updates"], "green")

    @patch("app.get_updates_categorized")
    @patch("app.get_security_config")
    def test_updates_optional_yellow(self, mock_get_security, mock_get_updates):
        mock_get_security.return_value = {"ufw": {"installed": True, "active": True}, "ssh": {"config": "PermitRootLogin no\n"}}
        mock_get_updates.return_value = {"total": 1, "categories": {"security": 0, "critical": 0, "necessary": 0, "optional": 1}}
        s = app_module._compute_system_status()
        self.assertEqual(s["updates"], "yellow")

    @patch("app.get_updates_categorized")
    @patch("app.get_security_config")
    def test_updates_security_or_critical_red(self, mock_get_security, mock_get_updates):
        mock_get_security.return_value = {"ufw": {"installed": True, "active": True}, "ssh": {"config": "PermitRootLogin no\n"}}
        mock_get_updates.return_value = {"total": 2, "categories": {"security": 1, "critical": 0, "necessary": 1, "optional": 0}}
        s = app_module._compute_system_status()
        self.assertEqual(s["updates"], "red")


if __name__ == "__main__":
    unittest.main()

