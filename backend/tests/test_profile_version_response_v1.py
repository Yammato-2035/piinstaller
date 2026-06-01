"""Version API profile and frontend alignment."""

from __future__ import annotations

import unittest

from core.install_profile import audit_frontend_backend_profile


class ProfileVersionResponseTests(unittest.TestCase):
    def test_frontend_release_backend_local_lab_mismatch(self) -> None:
        audit = audit_frontend_backend_profile(
            frontend_build_profile="release",
            backend_profile="local_lab",
        )
        self.assertTrue(audit["frontend_profile_mismatch"])

    def test_frontend_local_lab_backend_release_mismatch(self) -> None:
        audit = audit_frontend_backend_profile(
            frontend_build_profile="local_lab",
            backend_profile="release",
        )
        self.assertTrue(audit["frontend_profile_mismatch"])

    def test_matching_profiles_ok(self) -> None:
        audit = audit_frontend_backend_profile(
            frontend_build_profile="local_lab",
            backend_profile="local_lab",
        )
        self.assertFalse(audit["frontend_profile_mismatch"])


if __name__ == "__main__":
    unittest.main()
