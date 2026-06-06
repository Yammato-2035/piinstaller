"""Tauri-Konfiguration: kein unzulaessiges Setuphelfer-Top-Level-Feld."""

import json
import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
_repo = _backend.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core import version_projection as vp  # noqa: E402

_TAURI_CONF = _repo / "frontend" / "src-tauri" / "tauri.conf.json"
_RESOURCE = _repo / "frontend" / "src-tauri" / "resources" / "setuphelfer-version.json"
_RENAME_SCRIPT = _repo / "scripts" / "rename-tauri-bundle-artifacts.sh"

# Tauri 2 erlaubte Top-Level-Keys (keine Setuphelfer-Erweiterungen).
_TAURI_ALLOWED_TOP_LEVEL = frozenset(
    {
        "$schema",
        "productName",
        "version",
        "identifier",
        "build",
        "app",
        "bundle",
        "plugins",
    }
)

_FORBIDDEN_SETUPHELFER_TOP_LEVEL = frozenset({"setuphelferProjectVersion"})


class TauriConfigSchemaTests(unittest.TestCase):
    def test_tauri_conf_has_no_setuphelfer_project_version_field(self) -> None:
        data = json.loads(_TAURI_CONF.read_text(encoding="utf-8"))
        self.assertNotIn("setuphelferProjectVersion", data)

    def test_tauri_conf_no_forbidden_setuphelfer_top_level_metadata(self) -> None:
        data = json.loads(_TAURI_CONF.read_text(encoding="utf-8"))
        for key in _FORBIDDEN_SETUPHELFER_TOP_LEVEL:
            self.assertNotIn(key, data)
        for key in data:
            self.assertFalse(
                key.startswith("setuphelfer"),
                msg=f"forbidden setuphelfer top-level key: {key}",
            )

    def test_tauri_conf_only_allowed_top_level_keys(self) -> None:
        data = json.loads(_TAURI_CONF.read_text(encoding="utf-8"))
        extra = set(data.keys()) - _TAURI_ALLOWED_TOP_LEVEL
        self.assertEqual(extra, set(), msg=f"unexpected top-level keys: {sorted(extra)}")

    def test_deb_changelog_is_file_path_not_inline_text(self) -> None:
        data = json.loads(_TAURI_CONF.read_text(encoding="utf-8"))
        changelog = ((data.get("bundle") or {}).get("linux") or {}).get("deb", {}).get("changelog")
        self.assertEqual(changelog, "deb-changelog.txt")
        deb_changelog = _repo / "frontend" / "src-tauri" / "deb-changelog.txt"
        self.assertTrue(deb_changelog.is_file())
        self.assertNotIn("\n", changelog or "")

    def test_tauri_bundle_includes_version_resource(self) -> None:
        data = json.loads(_TAURI_CONF.read_text(encoding="utf-8"))
        resources = (data.get("bundle") or {}).get("resources") or []
        self.assertIn("resources/setuphelfer-version.json", resources)
        self.assertTrue(_RESOURCE.is_file(), msg=str(_RESOURCE))

    def test_version_resource_matches_config_version_json(self) -> None:
        cfg = json.loads((_repo / "config" / "version.json").read_text(encoding="utf-8"))
        res = json.loads(_RESOURCE.read_text(encoding="utf-8"))
        pv = str(cfg.get("project_version") or "")
        self.assertEqual(res.get("project_version"), pv)
        projection = vp.build_version_projection(pv)
        self.assertEqual(res.get("semver_package_version"), projection.semver_package_version)

    def test_version_projection_still_valid_for_current_repo(self) -> None:
        out = vp.build_version_projection_from_repo(_repo)
        self.assertEqual(out.project_version, "1.7.4.2")
        self.assertEqual(out.semver_package_version, "1.7.4")

    def test_rename_script_target_deb_name_matches_projection(self) -> None:
        projection = vp.build_version_projection("1.7.3.1")
        self.assertEqual(projection.expected_artifact_names()["deb"], "SetupHelfer_1.7.3.1_amd64.deb")
        self.assertTrue(_RENAME_SCRIPT.is_file())


if __name__ == "__main__":
    unittest.main()
