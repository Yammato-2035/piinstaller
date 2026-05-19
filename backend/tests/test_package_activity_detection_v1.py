"""UPDATE-CONFLICT-041: Paketaktivität — apt list (read-only) vs apt-get (blockierend)."""

from __future__ import annotations

import unittest

from core.package_activity import is_blocking_package_activity


class PackageActivityDetectionTests(unittest.TestCase):
    def test_apt_list_not_blocking(self) -> None:
        hay = "apt /usr/bin/apt list --upgradable"
        self.assertFalse(is_blocking_package_activity(hay, "apt"))

    def test_apt_get_upgrade_blocking(self) -> None:
        hay = "apt-get /usr/bin/apt-get upgrade -y"
        self.assertTrue(is_blocking_package_activity(hay, "apt-get"))

    def test_apt_get_update_not_blocking(self) -> None:
        hay = "apt-get apt-get update -qq"
        self.assertFalse(is_blocking_package_activity(hay, "apt-get"))

    def test_sh_apt_get_update_not_blocking(self) -> None:
        hay = "sh /bin/sh -c apt-get update -qq 2>/dev/null"
        self.assertFalse(is_blocking_package_activity(hay, "sh"))

    def test_dpkg_configure_blocking(self) -> None:
        hay = "dpkg dpkg --configure -a"
        self.assertTrue(is_blocking_package_activity(hay, "dpkg"))

    def test_unattended_shutdown_not_blocking(self) -> None:
        hay = "python3 unattended-upgrade-shutdown --wait-for-signal"
        self.assertFalse(is_blocking_package_activity(hay, "python3"))

    def test_systemctl_stop_apt_daily_unit_not_blocking(self) -> None:
        hay = "systemctl stop apt-daily.service apt-daily-upgrade.service"
        self.assertFalse(is_blocking_package_activity(hay, "systemctl"))

    def test_apt_get_upgrade_simulate_not_blocking(self) -> None:
        hay = "sh /bin/sh -c apt-get upgrade -s nvidia-utils-595 2>/dev/null | grep -i security"
        self.assertFalse(is_blocking_package_activity(hay, "sh"))

    def test_apt_get_install_simulate_not_blocking(self) -> None:
        hay = "apt-get /usr/bin/apt-get install -s curl"
        self.assertFalse(is_blocking_package_activity(hay, "apt-get"))


if __name__ == "__main__":
    unittest.main()
