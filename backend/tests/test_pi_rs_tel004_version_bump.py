"""PI-RS-TEL-004 version bump verification (tracks current project_version)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


class Tel004VersionBumpTests(unittest.TestCase):
    def test_project_version_is_current(self) -> None:
        root = Path(__file__).resolve().parents[2]
        version_json = json.loads((root / "config/version.json").read_text(encoding="utf-8"))
        self.assertEqual(version_json["project_version"], "1.9.20.0")
        self.assertEqual((root / "VERSION").read_text(encoding="utf-8").strip(), "1.9.20.0")

    def test_old_patch_not_default_in_version_json(self) -> None:
        root = Path(__file__).resolve().parents[2]
        version_json = json.loads((root / "config/version.json").read_text(encoding="utf-8"))
        self.assertNotEqual(version_json["project_version"], "1.9.19.4")


if __name__ == "__main__":
    unittest.main()
