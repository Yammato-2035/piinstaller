"""PI-RS-TEL-003 version bump verification (historical pin superseded)."""

from __future__ import annotations

from core.versioning import get_project_version

# TEL-003 raised the project version to 1.9.19.4; TEL-004 to 1.9.19.5.
# Later tracks (compat/baseline) advanced to 1.10.x — keep a floor check only.
_TEL003_FLOOR = (1, 9, 19, 4)


def _parse(v: str) -> tuple[int, ...]:
    return tuple(int(p) for p in v.strip().split("."))


def test_project_version_bumped_for_pi_rs_tel_003():
    current = get_project_version()
    assert _parse(current) >= _TEL003_FLOOR, current
    assert current != "1.9.19.4"
