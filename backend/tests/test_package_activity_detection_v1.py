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

    def test_dpkg_configure_blocking(self) -> None:
        hay = "dpkg dpkg --configure -a"
        self.assertTrue(is_blocking_package_activity(hay, "dpkg"))

    def test_unattended_shutdown_not_blocking(self) -> None:
        hay = "python3 unattended-upgrade-shutdown --wait-for-signal"
        self.assertFalse(is_blocking_package_activity(hay, "python3"))


if __name__ == "__main__":
    unittest.main()
