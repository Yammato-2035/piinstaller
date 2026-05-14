"""Deployment-Manifest: Generator und deploy_drift-Leselogik."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core import deploy_manifest as dm  # noqa: E402
from core import dev_dashboard as dd  # noqa: E402


def _touch(p: Path, content: bytes = b"x") -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content)


class DeployManifestGeneratorTests(unittest.TestCase):
    def _minimal_repo(self, tmp: Path) -> None:
        for rel in dm.DEPLOY_MANIFEST_REL_PATHS:
            _touch(tmp / rel, b"#stub\n")
        (tmp / "config" / "version.json").write_text(
            json.dumps(
                {
                    "project_version": "9.8.7",
                    "release_stage": "internal_testing",
                    "version_source_of_truth": True,
                    "version_track": "t",
                }
            ),
            encoding="utf-8",
        )

    def test_build_manifest_contains_expected_fields(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._minimal_repo(root)
            data = dm.build_manifest_data(root)
        self.assertEqual(data.get("manifest_version"), dm.MANIFEST_VERSION)
        self.assertEqual(data.get("project_version"), "9.8.7")
        self.assertIn("files", data)
        self.assertEqual(len(data["files"]), len(dm.DEPLOY_MANIFEST_REL_PATHS))
        rels = {str(x["relative_path"]) for x in data["files"]}
        self.assertEqual(rels, set(dm.DEPLOY_MANIFEST_REL_PATHS))

    def test_build_manifest_rejects_forbidden_path(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._minimal_repo(root)
            with patch.object(dm, "DEPLOY_MANIFEST_REL_PATHS", ("node_modules/x.js",)):
                with self.assertRaises(dm.DeployManifestError) as ctx:
                    dm.build_manifest_data(root)
        self.assertIn("forbidden", str(ctx.exception).lower())

    def test_build_manifest_fails_missing_required_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._minimal_repo(root)
            (root / "backend" / "app.py").unlink()
            with self.assertRaises(dm.DeployManifestError) as ctx:
                dm.build_manifest_data(root)
        self.assertIn("missing_required_file", str(ctx.exception))

    def test_compare_manifests_match_fixture(self) -> None:
        fx = _backend.parent / "tests" / "fixtures" / "deploy" / "sample-setuphelfer-deploy-manifest.json"
        raw = json.loads(fx.read_text(encoding="utf-8"))
        ok, warns = dm.compare_manifest_payloads(raw, raw)
        self.assertTrue(ok)
        self.assertEqual(warns, [])

    def test_deploy_drift_tolerates_missing_runtime_manifest(self) -> None:
        import hashlib

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td) / "w"
            rt = Path(td) / "r"
            ws.mkdir()
            rt.mkdir()
            content = b"a"
            hx = hashlib.sha256(content).hexdigest()
            man = {
                "manifest_version": 1,
                "generated_at": "2026-01-01T00:00:00+00:00",
                "project_version": "1.0.0",
                "release_stage": "internal_testing",
                "version_track": "t",
                "git_commit": None,
                "git_branch": None,
                "workspace_root": str(ws),
                "app_edition": "test",
                "files": [
                    {
                        "relative_path": "z.txt",
                        "sha256": hx,
                        "size_bytes": len(content),
                        "kind": "backend",
                        "required_runtime": True,
                    }
                ],
            }
            (ws / "build" / "deploy").mkdir(parents=True, exist_ok=True)
            (ws / "build" / "deploy" / dm.MANIFEST_BASENAME).write_text(json.dumps(man), encoding="utf-8")
            with patch.object(dd, "DEPLOY_DRIFT_REL_PATHS", ("z.txt",)):
                (ws / "z.txt").write_bytes(content)
                (rt / "z.txt").write_bytes(content)
                out = dd._compute_deploy_drift(workspace_root=ws, runtime_root=rt)
        self.assertIn("runtime_manifest_missing", out.get("manifest_warnings") or [])
        self.assertIn("deploy_manifest_optional", out.get("suggested_actions") or [])

    def test_deploy_drift_workspace_manifest_missing_warning(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td) / "w"
            rt = Path(td) / "r"
            ws.mkdir()
            rt.mkdir()
            with patch.object(dd, "DEPLOY_DRIFT_REL_PATHS", ("z.txt",)):
                (ws / "z.txt").write_text("a", encoding="utf-8")
                (rt / "z.txt").write_text("a", encoding="utf-8")
                out = dd._compute_deploy_drift(workspace_root=ws, runtime_root=rt)
        self.assertIn("workspace_manifest_missing", out.get("manifest_warnings") or [])
        self.assertIn("generate_deploy_manifest", out.get("suggested_actions") or [])

    def test_cli_generate_script_writes_json(self) -> None:
        import subprocess

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._minimal_repo(root)
            script = _backend / "tools" / "generate_deploy_manifest.py"
            out = root / "custom-manifest.json"
            subprocess.check_call(
                [sys.executable, str(script), "--repo-root", str(root), "--output", str(out)],
                cwd=str(_backend),
            )
            self.assertTrue(out.is_file())
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data.get("manifest_version"), dm.MANIFEST_VERSION)


if __name__ == "__main__":
    unittest.main()
