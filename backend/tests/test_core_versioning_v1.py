from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.versioning import get_project_version, get_release_stage, load_project_version


class CoreVersioningV1Tests(unittest.TestCase):
    def test_gueltige_zentrale_version(self) -> None:
        info = load_project_version()
        self.assertEqual(info.project_version, get_project_version())
        self.assertEqual(info.release_stage, "internal_testing")
        self.assertEqual(get_release_stage(), "internal_testing")

    def test_ungueltige_release_stage_blockiert(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "version.json"
            p.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "project_version": "1.6.0",
                        "release_stage": "broken",
                        "version_track": "x",
                        "version_source_of_truth": True,
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_project_version(version_file=p)


if __name__ == "__main__":
    unittest.main()
