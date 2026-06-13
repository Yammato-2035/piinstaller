"""Phase G.13: System Runtime Info Core contract tests."""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path
from unittest import mock

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

CORE_PATH = _BACKEND / "core" / "system_runtime_info.py"
FACADE_PATH = _BACKEND / "core" / "system_status_facade.py"

PUBLIC_FUNCTIONS = (
    "build_runtime_info",
    "build_installation_info",
    "build_profile_info",
    "build_runtime_diagnostics",
    "get_app_edition",
)


class TestSystemRuntimeInfoV1(unittest.TestCase):
    def test_core_module_has_version_and_public_api(self) -> None:
        import core.system_runtime_info as core

        self.assertEqual(core.SYSTEM_RUNTIME_INFO_VERSION, 1)
        for name in PUBLIC_FUNCTIONS:
            self.assertTrue(hasattr(core, name), f"missing {name}")
            self.assertTrue(callable(getattr(core, name)))

    def test_core_ast_has_no_app_import(self) -> None:
        tree = ast.parse(CORE_PATH.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotEqual(alias.name, "app")
            if isinstance(node, ast.ImportFrom) and node.module:
                self.assertFalse(node.module == "app" or node.module.startswith("app."))

    def test_facade_has_no_app_import_g13(self) -> None:
        tree = ast.parse(FACADE_PATH.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotEqual(alias.name, "app")
            if isinstance(node, ast.ImportFrom) and node.module:
                self.assertFalse(node.module == "app" or node.module.startswith("app."))

    def test_build_runtime_info_shape(self) -> None:
        import core.system_runtime_info as core

        with (
            mock.patch("core.system_runtime_info.get_project_version", return_value="1.7.14.0"),
            mock.patch("core.system_runtime_info.get_app_edition", return_value="repo"),
            mock.patch("core.system_runtime_info.get_backend_runtime_dir", return_value=Path("/opt/setuphelfer/backend")),
        ):
            out = core.build_runtime_info()
        self.assertEqual(out["version"], "1.7.14.0")
        self.assertEqual(out["edition"], "repo")
        self.assertIn("runtime_path", out)

    def test_facade_uses_system_runtime_info(self) -> None:
        text = FACADE_PATH.read_text(encoding="utf-8")
        self.assertIn("system_runtime_info", text)
        self.assertIn("build_runtime_info", text)
        self.assertIn("build_installation_info", text)
        self.assertIn("build_profile_info", text)


if __name__ == "__main__":
    unittest.main()
