"""Profile deploy manifest loading."""

from __future__ import annotations

import unittest
from pathlib import Path

from core.profile_deploy_manifest import load_profile_manifest, repo_root


class ProfileDeployManifestTests(unittest.TestCase):
    def test_release_manifest_forbids_dev_api(self) -> None:
        m = load_profile_manifest("release", repo_root())
        forbidden = m.get("forbidden_api_paths") or []
        self.assertIn("/api/fleet", forbidden)
        self.assertIn("/api/rescue-remote", forbidden)

    def test_local_lab_manifest_allows_dev_api(self) -> None:
        m = load_profile_manifest("local_lab", repo_root())
        required = m.get("required_api_paths") or []
        self.assertIn("/api/dev-diagnostics", required)

    def test_manifest_files_exist(self) -> None:
        for prof in ("release", "local_lab", "developer", "rescue_lab"):
            p = repo_root() / "deploy" / "manifests" / f"{prof}.manifest.json"
            self.assertTrue(p.is_file(), prof)


if __name__ == "__main__":
    unittest.main()
