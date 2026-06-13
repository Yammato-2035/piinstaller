"""Phase G.9: system_info_facade no longer depends on lazy app imports."""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

FACADE_PATH = _BACKEND / "core" / "system_info_facade.py"
APP_PY = _BACKEND / "app.py"

LEGACY_WRAPPERS = (
    ("def get_cpu_temp", "get_cpu_temp"),
    ("def get_cpu_name", "get_cpu_name"),
    ("def get_cpu_summary", "get_cpu_summary"),
    ("def get_motherboard_info", "get_motherboard_info"),
    ("def get_ram_info", "get_ram_info"),
    ("def _get_pci_with_drivers", "_get_pci_with_drivers"),
    ("def _get_gpus_for_system_info", "_get_gpus_for_system_info"),
    ("def _get_pi_config_module", "_get_pi_config_module"),
)


class TestSystemInfoWithoutAppDependencyG9(unittest.TestCase):
    def test_facade_ast_has_no_app_import(self) -> None:
        tree = ast.parse(FACADE_PATH.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotEqual(alias.name, "app")
            if isinstance(node, ast.ImportFrom) and node.module:
                self.assertFalse(node.module == "app" or node.module.startswith("app."))

    def test_facade_source_mentions_hardware_discovery(self) -> None:
        text = FACADE_PATH.read_text(encoding="utf-8")
        self.assertIn("core.hardware_discovery", text)
        self.assertIn("discover_cpu_info", text)
        self.assertNotIn("_legacy_", text)
        self.assertNotIn("import app", text)

    def test_app_legacy_wrappers_delegate_to_hardware_discovery(self) -> None:
        text = APP_PY.read_text(encoding="utf-8")
        for marker, core_fn in LEGACY_WRAPPERS:
            start = text.index(marker)
            block = text[start : start + 250]
            self.assertIn("hardware_discovery", block, marker)
            self.assertIn(core_fn, block, marker)

    def test_diagnostics_delegate_to_hardware_discovery(self) -> None:
        import core.system_info_facade as facade

        diag = facade.build_system_info_diagnostics()
        joined = " ".join(diag.get("delegates_to", []))
        self.assertIn("hardware_discovery.discover_cpu_info", joined)
        self.assertNotIn("app.get_cpu_temp", joined)
        self.assertTrue(diag.get("hardware_via_hardware_discovery"))


if __name__ == "__main__":
    unittest.main()
