"""Post-Deploy-Verifikation: /opt-Dateien und OpenAPI-Routen."""

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
from core import deploy_runtime_verify as drv  # noqa: E402


class DeployRuntimeVerifyTests(unittest.TestCase):
    def test_manifest_includes_compact_status_module(self) -> None:
        self.assertIn(
            "backend/core/dev_dashboard_compact_status.py",
            dm.DEPLOY_MANIFEST_REL_PATHS,
        )

    def test_critical_paths_include_compact_status(self) -> None:
        self.assertIn(
            "backend/core/dev_dashboard_compact_status.py",
            drv.DEPLOY_RUNTIME_CRITICAL_REL_PATHS,
        )

    def test_verify_runtime_files_detects_missing_module(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ws = root / "workspace"
            rt = root / "runtime"
            ws.mkdir()
            rt.mkdir()
            rel = "backend/core/dev_dashboard_compact_status.py"
            content = b"# compact status module\n"
            (ws / rel).parent.mkdir(parents=True, exist_ok=True)
            (ws / rel).write_bytes(content)
            (rt / "backend" / "app.py").parent.mkdir(parents=True, exist_ok=True)
            (rt / "backend" / "app.py").write_text("# stub\n", encoding="utf-8")
            out = drv.verify_runtime_files(workspace_root=ws, runtime_root=rt, rel_paths=(rel,))
        self.assertFalse(out["ok"])
        self.assertIn(rel, out["missing_runtime"])

    def test_verify_runtime_files_ok_when_sha256_matches(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ws = root / "w"
            rt = root / "r"
            ws.mkdir()
            rt.mkdir()
            rel = "backend/core/dev_dashboard_compact_status.py"
            content = b"match me\n"
            for base in (ws, rt):
                p = base / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(content)
            out = drv.verify_runtime_files(workspace_root=ws, runtime_root=rt, rel_paths=(rel,))
        self.assertTrue(out["ok"])
        self.assertEqual(out["missing_runtime"], [])
        self.assertEqual(out["sha256_mismatch"], [])

    def test_verify_app_route_markers_detects_missing_compact_route(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            rt = Path(td)
            app = rt / "backend" / "app.py"
            app.parent.mkdir(parents=True)
            app.write_text("@app.get('/api/other')\n", encoding="utf-8")
            out = drv.verify_app_route_markers(runtime_root=rt)
        self.assertFalse(out["ok"])
        self.assertTrue(out["missing_markers"])

    def test_verify_openapi_paths_detects_missing_route(self) -> None:
        payload = {"paths": {"/api/version": {}}}
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(payload).encode()
            out = drv.verify_openapi_paths(base_url="http://127.0.0.1:8000")
        self.assertFalse(out["ok"])
        self.assertIn("/api/dev-dashboard/compact-status", out["missing_paths"])

    def test_verify_openapi_paths_ok_when_route_registered(self) -> None:
        payload = {"paths": {"/api/dev-dashboard/compact-status": {"get": {}}}}
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(payload).encode()
            out = drv.verify_openapi_paths(base_url="http://127.0.0.1:8000")
        self.assertTrue(out["ok"])
        self.assertEqual(out["missing_paths"], [])

    def test_run_post_rsync_verify_combines_checks(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td) / "w"
            rt = Path(td) / "r"
            ws.mkdir()
            rt.mkdir()
            rel = "backend/core/dev_dashboard_compact_status.py"
            for base in (ws, rt):
                p = base / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(b"x\n")
            app = rt / "backend" / "app.py"
            app.write_text(
                '@app.get("/api/dev-dashboard/compact-status")\nfrom core.dev_dashboard_compact_status import build_compact_dcc_status\n',
                encoding="utf-8",
            )
            out = drv.run_post_rsync_verify(workspace_root=ws, runtime_root=rt)
        self.assertTrue(out["ok"])


if __name__ == "__main__":
    unittest.main()
