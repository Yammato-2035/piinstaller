"""Phase G.1: System Status Facade contract tests."""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path
from unittest import mock

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

FACADE_PATH = _BACKEND / "core" / "system_status_facade.py"

PUBLIC_FUNCTIONS = (
    "build_system_status",
    "build_system_status_sections",
    "build_backend_runtime_section",
    "build_installation_section",
    "build_profile_section",
    "build_system_status_diagnostics",
    "normalize_legacy_system_status",
    "build_unavailable_section",
)


class TestSystemStatusFacadeV1(unittest.TestCase):
    def test_facade_module_has_version_and_public_api(self) -> None:
        import core.system_status_facade as facade

        self.assertEqual(facade.FACADE_VERSION, 1)
        for name in PUBLIC_FUNCTIONS:
            self.assertTrue(hasattr(facade, name), f"missing {name}")
            self.assertTrue(callable(getattr(facade, name)))

    def test_facade_source_has_no_subprocess_systemctl_sudo_calls(self) -> None:
        tree = ast.parse(FACADE_PATH.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                if node.value.id == "subprocess":
                    self.fail("subprocess attribute access in facade")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in {"system", "Popen", "run"}:
                    self.fail(f"unexpected call {node.func.id}")

    def test_facade_source_has_no_network_probe_imports(self) -> None:
        tree = ast.parse(FACADE_PATH.read_text(encoding="utf-8"))
        banned = {"get_network_info", "_demo_network", "get_network_info_facade"}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and "network" in node.module:
                self.fail(f"network import from {node.module}")
            if isinstance(node, ast.Name) and node.id in banned:
                parent = getattr(node, "parent", None)
                if isinstance(parent, ast.Call):
                    self.fail(f"network call {node.id}")

    def test_facade_import_ast_no_module_level_app_import(self) -> None:
        tree = ast.parse(FACADE_PATH.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertNotEqual(alias.name, "app")
                if isinstance(node, ast.ImportFrom) and node.module == "app":
                    self.fail("module-level import from app")

    def test_normalize_legacy_system_status_maps_ampel(self) -> None:
        from core.system_status_facade import normalize_legacy_system_status

        out = normalize_legacy_system_status(
            {"backup": "green", "restore": "yellow", "security": "red", "updates": "green"}
        )
        self.assertEqual(out["status"], "blocked")
        self.assertEqual(out["ampel"]["backup"], "ok")
        self.assertEqual(out["ampel"]["security"], "blocked")

    def test_build_unavailable_section_shape(self) -> None:
        from core.system_status_facade import build_unavailable_section

        sec = build_unavailable_section("test", reason="x")
        self.assertEqual(sec.status, "unavailable")
        self.assertEqual(sec.section_id, "test")

    def test_section_failure_does_not_crash_sections(self) -> None:
        from core.system_status_facade import build_system_status_sections

        with mock.patch(
            "core.system_status_facade._legacy_compute_ampel_status",
            side_effect=RuntimeError("boom"),
        ), mock.patch(
            "core.system_status_facade.build_backend_runtime_section",
            return_value={
                "section_id": "backend_runtime",
                "status": "ok",
                "data": {"version": "1.0.0"},
                "warnings": [],
                "errors": [],
            },
        ), mock.patch(
            "core.system_status_facade.build_installation_section",
            return_value={
                "section_id": "installation",
                "status": "ok",
                "data": {},
                "warnings": [],
                "errors": [],
            },
        ), mock.patch(
            "core.system_status_facade.build_profile_section",
            return_value={
                "section_id": "profile",
                "status": "ok",
                "data": {},
                "warnings": [],
                "errors": [],
            },
        ):
            out = build_system_status_sections()
        self.assertEqual(out["facade_version"], 1)
        self.assertGreaterEqual(len(out["sections"]), 3)
        ampel = next(s for s in out["sections"] if s["section_id"] == "system_ampel")
        self.assertEqual(ampel["status"], "unavailable")
        self.assertTrue(out["errors"])

    def test_build_system_status_legacy_shape(self) -> None:
        from core.system_status_facade import build_system_status

        fake_ampel = {"backup": "green", "restore": "red", "security": "yellow", "updates": "green"}
        with mock.patch(
            "core.system_status_facade._legacy_compute_ampel_status",
            return_value=fake_ampel,
        ), mock.patch(
            "core.system_status_facade._legacy_backup_realtest_state",
            return_value={"last_verify_ok": True},
        ), mock.patch(
            "core.system_status_facade.build_backend_runtime_section",
            return_value={
                "section_id": "backend_runtime",
                "status": "ok",
                "data": {},
                "warnings": [],
                "errors": [],
            },
        ), mock.patch(
            "core.system_status_facade.build_installation_section",
            return_value={
                "section_id": "installation",
                "status": "ok",
                "data": {},
                "warnings": [],
                "errors": [],
            },
        ), mock.patch(
            "core.system_status_facade.build_profile_section",
            return_value={
                "section_id": "profile",
                "status": "ok",
                "data": {},
                "warnings": [],
                "errors": [],
            },
        ):
            out = build_system_status()
        self.assertEqual(out["status"], "success")
        self.assertEqual(out["backup"], "green")
        self.assertEqual(out["restore"], "red")
        self.assertEqual(out["realtest_state"]["last_verify_ok"], True)
        legacy_keys = {
            "status",
            "api_status",
            "message",
            "data",
            "backup",
            "restore",
            "security",
            "updates",
            "realtest_state",
        }
        self.assertEqual(set(out.keys()), legacy_keys)

    def test_diagnostics_present(self) -> None:
        from core.system_status_facade import build_system_status_diagnostics

        diag = build_system_status_diagnostics()
        self.assertEqual(diag["facade_version"], 1)
        self.assertIn("GET /api/status", diag["routes_pending_facade_migration"])
        self.assertNotIn("GET /api/system/status", diag["routes_pending_facade_migration"])
        self.assertFalse(diag["network_diagnostics_allowed"])
        for fn in PUBLIC_FUNCTIONS:
            self.assertIn(fn, diag["public_functions"])


if __name__ == "__main__":
    unittest.main()
