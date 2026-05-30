"""Tests für devserver.ssh_readonly."""

from __future__ import annotations

import unittest

from devserver.models import default_dev_node
from devserver.ssh_readonly import (
    SshReadonlyError,
    build_readonly_command_list,
    run_ssh_profile,
    validate_command_profile,
)


class DevServerSshReadonlyTests(unittest.TestCase):
    def test_free_commands_impossible(self) -> None:
        with self.assertRaises(SshReadonlyError):
            build_readonly_command_list("nonexistent_profile")

    def test_forbidden_tokens_blocked(self) -> None:
        forbidden_cmds = [
            "dd if=/dev/zero of=/dev/sda",
            "mkfs.ext4 /dev/sda1",
            "mount /dev/sda1 /mnt",
            "umount /mnt",
            "parted /dev/sda mklabel gpt",
            "sfdisk /dev/sda",
            "sgdisk -o /dev/sda",
            "wipefs -a /dev/sda",
            "sudo rm -rf /",
            "apt update",
            "rm -rf /tmp/x",
            "chmod 777 /etc",
            "chown root /etc",
            "systemctl restart ssh",
        ]
        for cmd in forbidden_cmds:
            with self.subTest(cmd=cmd):
                with self.assertRaises(SshReadonlyError):
                    from devserver.ssh_readonly import _validate_single_command
                    _validate_single_command(cmd)

    def test_ssh_disabled_blocks(self) -> None:
        node = default_dev_node(node_id="n1")
        node["ssh"]["enabled"] = False
        result = run_ssh_profile(node, "ssh_check")
        self.assertTrue(result["blocked"])

    def test_missing_node_ssh_config_blocks(self) -> None:
        node = default_dev_node(node_id="n1")
        node["ssh"]["enabled"] = True
        node["ssh"]["host"] = ""
        result = run_ssh_profile(node, "ssh_check")
        self.assertTrue(result["blocked"])

    def test_allowlist_profiles_only_allowed_commands(self) -> None:
        for profile in ("ssh_check", "collect_inventory", "collect_storage", "collect_boot"):
            self.assertTrue(validate_command_profile(profile))
            cmds = build_readonly_command_list(profile)
            self.assertGreater(len(cmds), 0)
            for cmd in cmds:
                self.assertNotIn("sudo", cmd)

    def test_stdout_stderr_truncated(self) -> None:
        node = default_dev_node(node_id="n1")
        node["ssh"] = {
            "enabled": True,
            "host": "127.0.0.1",
            "port": 22,
            "username": "lab",
            "auth_ref": "",
            "last_check_status": "not_configured",
            "last_check_error": "",
        }
        big = "x" * 100_000

        def fake_runner(_argv, _timeout):
            return {"exit_code": 0, "stdout": big, "stderr": big}

        result = run_ssh_profile(node, "ssh_check", runner=fake_runner)
        self.assertLessEqual(len(result["stdout"]), 70_000)
        self.assertIn("truncated", result["stdout"])


if __name__ == "__main__":
    unittest.main()
