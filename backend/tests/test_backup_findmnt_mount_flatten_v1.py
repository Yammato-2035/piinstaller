"""findmnt -J liefert verschachtelte children; _findmnt_mounts muss flach sein für target-check."""

from __future__ import annotations

import json
import unittest
from unittest.mock import patch

import app as app_module


class TestBackupFindmntMountFlattenV1(unittest.TestCase):
    def test_findmnt_mounts_flattens_nested_children(self) -> None:
        nested = {
            "filesystems": [
                {
                    "source": "/dev/nvme0n1p2",
                    "target": "/",
                    "fstype": "ext4",
                    "options": "rw",
                    "children": [
                        {
                            "source": "/dev/sdd1",
                            "target": "/media/gabriel/setuphelfer-back",
                            "fstype": "ext4",
                            "options": "rw,nosuid",
                            "children": [],
                        }
                    ],
                }
            ]
        }

        def fake_run(cmd: str, *args, **kwargs):
            if "findmnt -J" in cmd:
                return {"success": True, "stdout": json.dumps(nested)}
            return {"success": False, "stdout": ""}

        with patch.object(app_module, "run_command", side_effect=fake_run):
            mounts = app_module._findmnt_mounts()

        targets = {m.get("target") for m in mounts if isinstance(m, dict)}
        self.assertIn("/", targets)
        self.assertIn("/media/gabriel/setuphelfer-back", targets)
        self.assertGreaterEqual(len(mounts), 2)


if __name__ == "__main__":
    unittest.main()
