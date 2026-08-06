"""PI-RS-TEL-004 version bump verification (historical pin superseded)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

_TEL004_FLOOR = (1, 9, 19, 5)


def _parse(v: str) -> tuple[int, ...]:
    return tuple(int(p) for p in v.strip().split("."))


class Tel004VersionBumpTests(unittest.TestCase):
    def test_project_version_at_least_tel004_floor(self) -> None:
        root = Path(__file__).resolve().parents[2]
        version_json = json.loads((root / "config/version.json").read_text(encoding="utf-8"))
        project = version_json["project_version"]
        version_file = (root / "VERSION").read_text(encoding="utf-8").strip()
        self.assertEqual(project, version_file)
        self.assertGreaterEqual(_parse(project), _TEL004_FLOOR)

    def test_old_patch_not_default_in_version_json(self) -> None:
        root = Path(__file__).resolve().parents[2]
        version_json = json.loads((root / "config/version.json").read_text(encoding="utf-8"))
        self.assertNotEqual(version_json["project_version"], "1.9.19.4")


if __name__ == "__main__":
    unittest.main()
