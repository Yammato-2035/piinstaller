"""Tests fuer VersionProjection und Packaging-Gate."""

import sys
import tempfile
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core import version_projection as vp  # noqa: E402


class VersionProjectionTests(unittest.TestCase):
    def test_projection_for_1_7_3_1(self) -> None:
        p = vp.build_version_projection("1.7.3.1")
        self.assertEqual(p.project_version, "1.7.3.1")
        self.assertEqual(p.semver_package_version, "1.7.3")
        self.assertEqual(p.patch_component, 1)
        self.assertEqual(p.deb_upstream_version, "1.7.3.1")
        self.assertEqual(p.expected_artifact_names()["deb"], "SetupHelfer_1.7.3.1_amd64.deb")
        self.assertEqual(p.tauri_default_artifact_names()["deb"], "SetupHelfer_1.7.3_amd64.deb")

    def test_cargo_does_not_accept_four_part_semver(self) -> None:
        with self.assertRaises(ValueError):
            vp.parse_project_version("1.7.3")

    def test_classify_semver_artifact_as_projection_with_warning(self) -> None:
        p = vp.build_version_projection("1.7.3.1")
        info = vp.classify_bundle_filename("SetupHelfer_1.7.3_amd64.deb", p)
        self.assertTrue(info["ok"])
        self.assertEqual(info["match"], "semver_projection")
        self.assertTrue(info["misleading"])

    def test_classify_project_artifact_as_ok(self) -> None:
        p = vp.build_version_projection("1.7.3.1")
        info = vp.classify_bundle_filename("SetupHelfer_1.7.3.1_amd64.deb", p)
        self.assertTrue(info["ok"])
        self.assertEqual(info["match"], "project_version")
        self.assertFalse(info["misleading"])

    def test_packaging_check_warns_on_semver_only_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "config").mkdir()
            (root / "config" / "version.json").write_text(
                '{"project_version":"1.7.3.1","version_source_of_truth":true}',
                encoding="utf-8",
            )
            bundle = root / "frontend/src-tauri/target/release/bundle/deb"
            bundle.mkdir(parents=True)
            (bundle / "SetupHelfer_1.7.3_amd64.deb").write_bytes(b"x")
            out = vp.check_packaging_artifacts(repo_root=root)
        self.assertTrue(out["ok"])
        self.assertEqual(out["status"], "warn")
        self.assertTrue(out["warnings"])

    def test_packaging_check_blocks_conflicting_current_lineage(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "config").mkdir()
            (root / "config" / "version.json").write_text(
                '{"project_version":"1.7.3.1","version_source_of_truth":true}',
                encoding="utf-8",
            )
            bundle = root / "frontend/src-tauri/target/release/bundle/deb"
            bundle.mkdir(parents=True)
            (bundle / "SetupHelfer_1.7.3.0_amd64.deb").write_bytes(b"x")
            out = vp.check_packaging_artifacts(repo_root=root)
        self.assertFalse(out["ok"])
        self.assertEqual(out["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
