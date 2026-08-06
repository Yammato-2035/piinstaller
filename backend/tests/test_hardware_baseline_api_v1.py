"""PI-RS-HW-BASELINE-DIAG-I18N-002 Phase 12: rescue_hardware_baseline.py API tests.

Uses direct asyncio.run() handler invocation (no TestClient/httpx
dependency in this environment). Verifies read-only route inventory
(no forbidden write-style routes), app registration, and functional
behavior of status/quick/latest/subsystem routes.
"""

from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from fastapi import HTTPException

from api.routes import rescue_hardware_baseline as baseline_api

_FORBIDDEN_PATH_MARKERS = (
    "/apply",
    "/install",
    "/flash",
    "/write",
    "/format",
    "/partition",
    "/firmware/update",
    "/driver/install",
    "/self-test/start",
    "/self_test/start",
)

_EXPECTED_ROUTES = {
    "/api/rescue/hardware/baseline/status",
    "/api/rescue/hardware/baseline/quick",
    "/api/rescue/hardware/baseline/extended-preview",
    "/api/rescue/hardware/baseline/latest",
    "/api/rescue/hardware/baseline/memory",
    "/api/rescue/hardware/baseline/cpu",
    "/api/rescue/hardware/baseline/gpu",
    "/api/rescue/hardware/baseline/storage",
    "/api/rescue/hardware/baseline/storage/{device_id}",
}


class TestRouteInventory(unittest.TestCase):
    def test_all_expected_routes_exist(self) -> None:
        paths = {r.path for r in baseline_api.router.routes}
        self.assertEqual(paths, _EXPECTED_ROUTES)

    def test_no_forbidden_write_style_routes(self) -> None:
        for r in baseline_api.router.routes:
            for marker in _FORBIDDEN_PATH_MARKERS:
                self.assertNotIn(marker, r.path, f"forbidden path marker {marker!r} found in {r.path}")


class TestAppRegistration(unittest.TestCase):
    def test_routes_registered_on_main_app(self) -> None:
        import app as app_module

        app_paths = {r.path for r in app_module.app.routes if hasattr(r, "path")}
        for expected in _EXPECTED_ROUTES:
            self.assertIn(expected, app_paths)


class TestHandlersBeforeAnyRun(unittest.TestCase):
    def setUp(self) -> None:
        baseline_api._LAST_BASELINE.clear()

    def test_status_before_any_run_reports_has_run_false(self) -> None:
        status = asyncio.run(baseline_api.get_hardware_baseline_status())
        self.assertFalse(status["has_run"])

    def test_latest_before_run_raises_404(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(baseline_api.get_hardware_baseline_latest())
        self.assertEqual(ctx.exception.status_code, 404)


class TestHandlersAreReadOnlyAndDoNotCrash(unittest.TestCase):
    """A single real quick-baseline run (real dmesg/smartctl/nvme-cli calls
    against this host) is expensive; every test in this class reuses the
    one run performed in setUpClass instead of triggering a fresh scan."""

    @classmethod
    def setUpClass(cls) -> None:
        baseline_api._LAST_BASELINE.clear()
        cls.quick_result = asyncio.run(baseline_api.post_hardware_baseline_quick())

    def test_quick_run_does_not_crash_and_is_read_only(self) -> None:
        self.assertIn("run_id", self.quick_result)
        self.assertIn("gate", self.quick_result)
        self.assertIn("subsystems", self.quick_result)

    def test_status_reflects_last_run(self) -> None:
        status = asyncio.run(baseline_api.get_hardware_baseline_status())
        self.assertTrue(status["has_run"])
        self.assertIn("gate", status)

    def test_memory_subsystem_route(self) -> None:
        memory = asyncio.run(baseline_api.get_hardware_baseline_memory())
        self.assertEqual(memory["subsystem"], "memory")

    def test_cpu_subsystem_route(self) -> None:
        cpu = asyncio.run(baseline_api.get_hardware_baseline_cpu())
        self.assertEqual(cpu["subsystem"], "cpu")

    def test_gpu_subsystem_route(self) -> None:
        gpu = asyncio.run(baseline_api.get_hardware_baseline_gpu())
        self.assertEqual(gpu["subsystem"], "gpu")

    def test_storage_route_returns_device_list(self) -> None:
        storage = asyncio.run(baseline_api.get_hardware_baseline_storage())
        self.assertIn("devices", storage)

    def test_storage_device_route_404_for_unknown_device(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(baseline_api.get_hardware_baseline_storage_device("nonexistent-device-xyz"))
        self.assertEqual(ctx.exception.status_code, 404)


class TestExtendedPreviewMode(unittest.TestCase):
    def test_extended_preview_run_does_not_crash(self) -> None:
        baseline_api._LAST_BASELINE.clear()
        result = asyncio.run(baseline_api.post_hardware_baseline_extended_preview())
        self.assertEqual(result["mode"], "extended_preview")


if __name__ == "__main__":
    unittest.main()
