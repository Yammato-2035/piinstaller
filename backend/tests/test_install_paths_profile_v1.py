from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.install_paths import get_backend_runtime_dir, get_install_profile  # noqa: E402


class InstallPathsProfileV1Tests(unittest.TestCase):
    def test_backend_runtime_dir_ends_with_backend(self) -> None:
        p = get_backend_runtime_dir()
        self.assertTrue(str(p).rstrip("/").endswith("backend"))
        self.assertTrue((p / "app.py").is_file())

    def test_install_profile_repo_in_workspace(self) -> None:
        self.assertEqual(get_install_profile(), "repo")


if __name__ == "__main__":
    unittest.main()
