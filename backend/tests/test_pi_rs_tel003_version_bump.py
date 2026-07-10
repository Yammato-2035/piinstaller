"""PI-RS-TEL-003 version bump verification."""

from __future__ import annotations

from core.versioning import get_project_version


def test_project_version_bumped_for_pi_rs_tel_003():
    assert get_project_version() == "1.9.19.4"
