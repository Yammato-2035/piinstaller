"""Tests für Workspace-/Runtime-Versionskonsistenz."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core import version_consistency as vc  # noqa: E402


def _write_version_tree(root: Path, project_version: str = "1.7.3.1") -> None:
    semver = vc.semver_triple(project_version)
    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / "config" / "version.json").write_text(
        json.dumps(
            {
                "project_version": project_version,
                "release_stage": "internal_testing",
                "version_source_of_truth": True,
                "version_track": "t",
            }
        ),
        encoding="utf-8",
    )
    (root / "VERSION").write_text(project_version + "\n", encoding="utf-8")
    (root / "package.json").write_text(json.dumps({"version": project_version}) + "\n", encoding="utf-8")
    (root / "frontend").mkdir(parents=True, exist_ok=True)
    (root / "frontend" / "package.json").write_text(json.dumps({"version": project_version}) + "\n", encoding="utf-8")
    (root / "frontend" / "package-lock.json").write_text(
        json.dumps({"version": project_version, "packages": {"": {"version": project_version}}}) + "\n",
        encoding="utf-8",
    )
    tauri_dir = root / "frontend" / "src-tauri"
    tauri_dir.mkdir(parents=True, exist_ok=True)
    (tauri_dir / "tauri.conf.json").write_text(json.dumps({"version": semver}) + "\n", encoding="utf-8")
    (tauri_dir / "Cargo.toml").write_text(f'[package]\nname = "x"\nversion = "{semver}"\n', encoding="utf-8")


class VersionConsistencyTests(unittest.TestCase):
    def test_semver_triple_from_four_part_version(self) -> None:
        self.assertEqual(vc.semver_triple("1.7.3.1"), "1.7.3")

    def test_workspace_consistency_ok(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_version_tree(root)
            out = vc.check_workspace_consistency(root)
        self.assertTrue(out["ok"])
        self.assertEqual(out["canonical"], "1.7.3.1")

    def test_workspace_consistency_detects_frontend_drift(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_version_tree(root, "1.7.3.1")
            pkg = json.loads((root / "frontend" / "package.json").read_text(encoding="utf-8"))
            pkg["version"] = "1.7.3.0"
            (root / "frontend" / "package.json").write_text(json.dumps(pkg) + "\n", encoding="utf-8")
            out = vc.check_workspace_consistency(root)
        self.assertFalse(out["ok"])
        self.assertTrue(any("frontend/package.json" in mm for mm in out["mismatches"]))

    def test_runtime_consistency_detects_opt_drift(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            ws = base / "ws"
            rt = base / "rt"
            _write_version_tree(ws, "1.7.3.1")
            _write_version_tree(rt, "1.7.3.0")
            out = vc.check_runtime_consistency(
                workspace_root=ws,
                runtime_root=rt,
                api_project_version="1.7.3.0",
            )
        self.assertFalse(out["ok"])
        self.assertTrue(any("runtime/config/version.json" in mm for mm in out["mismatches"]))
        self.assertTrue(any("api/project_version" in mm for mm in out["mismatches"]))

    def test_manifest_includes_compact_status_after_bump(self) -> None:
        from core import deploy_manifest as dm

        self.assertIn("backend/core/dev_dashboard_compact_status.py", dm.DEPLOY_MANIFEST_REL_PATHS)


if __name__ == "__main__":
    unittest.main()
