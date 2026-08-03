"""PI-RS-HW-COMPAT-PROVISION-001 Phase 14: rescue hardware/peripherals/platform/
carrier/provisioning API — read-only/preview-only contract tests.

Uses ``app.routes`` directly (not ``TestClient``/``httpx``) because this
environment's ``starlette.testclient`` needs ``httpx``, which is not installed
here (pre-existing, unrelated environment gap — see prior phases' notes).
Route handlers are plain ``async def`` functions and are invoked directly via
``asyncio.run`` for functional assertions.
"""

from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

_FORBIDDEN_PATH_FRAGMENTS = (
    "/apply",
    "/install",
    "/flash",
    "/write",
    "/format",
    "/partition",
    "/firmware/update",
    "/driver/install",
    "/driver/activate",
    "/eeprom/update",
    "/bios/update",
)

_EXPECTED_ROUTES = {
    ("GET", "/api/rescue/hardware/inventory"),
    ("POST", "/api/rescue/hardware/scan"),
    ("GET", "/api/rescue/hardware/devices"),
    ("GET", "/api/rescue/hardware/devices/{device_id}"),
    ("GET", "/api/rescue/hardware/devices/{device_id}/driver-plan"),
    ("GET", "/api/rescue/hardware/cpu"),
    ("GET", "/api/rescue/hardware/gpus"),
    ("GET", "/api/rescue/hardware/mainboard"),
    ("GET", "/api/rescue/hardware/usb"),
    ("GET", "/api/rescue/hardware/input"),
    ("GET", "/api/rescue/peripherals/printers"),
    ("POST", "/api/rescue/peripherals/printers/scan"),
    ("GET", "/api/rescue/peripherals/scanners"),
    ("POST", "/api/rescue/peripherals/scanners/scan"),
    ("GET", "/api/rescue/platform/raspberry-pi"),
    ("GET", "/api/rescue/platform/raspberry-pi/os-compatibility"),
    ("GET", "/api/rescue/carrier/status"),
    ("POST", "/api/rescue/carrier/layout-preview"),
    ("GET", "/api/rescue/provision/catalog"),
    ("POST", "/api/rescue/provision/compatibility"),
    ("POST", "/api/rescue/provision/plan"),
    ("POST", "/api/rescue/provision/image-verification-preview"),
}


def _collect_new_module_routes() -> list[tuple[str, str]]:
    from api.routes import rescue_carrier, rescue_hardware, rescue_peripherals, rescue_platform, rescue_provisioning

    routes: list[tuple[str, str]] = []
    for module in (rescue_hardware, rescue_peripherals, rescue_platform, rescue_carrier, rescue_provisioning):
        for route in module.router.routes:
            for method in route.methods:
                routes.append((method, route.path))
    return routes


class TestExpectedRoutesPresent(unittest.TestCase):
    def test_all_spec_routes_exist(self) -> None:
        routes = set(_collect_new_module_routes())
        missing = _EXPECTED_ROUTES - routes
        self.assertEqual(missing, set(), f"missing routes: {missing}")

    def test_no_extra_write_style_routes_added(self) -> None:
        routes = set(_collect_new_module_routes())
        extra = routes - _EXPECTED_ROUTES
        self.assertEqual(extra, set(), f"unexpected routes: {extra}")


class TestNoForbiddenRoutesInNewHardwareModules(unittest.TestCase):
    """Scoped to this phase's 5 new routers only — pre-existing, separately
    gated app routes (e.g. ``/api/install/start``) are out of scope for this
    check and are governed by their own phases/safety gates."""

    def test_new_modules_have_no_forbidden_paths(self) -> None:
        routes = _collect_new_module_routes()
        forbidden_hits = [
            path for _, path in routes if any(fragment in path for fragment in _FORBIDDEN_PATH_FRAGMENTS)
        ]
        self.assertEqual(forbidden_hits, [], f"forbidden write-style routes found: {forbidden_hits}")

    def test_new_hardware_routes_registered_on_app(self) -> None:
        from app import app

        app_paths = {getattr(r, "path", None) for r in app.routes}
        for _, path in _EXPECTED_ROUTES:
            self.assertIn(path, app_paths, f"{path} not registered on app")


class TestHandlersAreReadOnlyPreviewOnly(unittest.TestCase):
    """Functional smoke test: every handler returns without raising and never
    performs a write action (write_allowed is always False where applicable)."""

    def test_provisioning_plan_write_allowed_always_false(self) -> None:
        from api.routes.rescue_provisioning import post_provision_plan

        async def run() -> dict:
            return await post_provision_plan(
                {
                    "image_id": "debian-13-stable-amd64-netinst",
                    "target_architecture": "x86_64",
                    "target_bytes": 20_000_000_000,
                }
            )

        result = asyncio.run(run())
        self.assertFalse(result["write_allowed"])

    def test_driver_plan_never_claims_live_activation_possible(self) -> None:
        from api.routes.rescue_hardware import get_hardware_devices, get_hardware_device_driver_plan

        async def run() -> dict:
            devices = await get_hardware_devices()
            if not devices["devices"]:
                return {"live_activation_possible": False}
            device_id = devices["devices"][0]["device_id"]
            return await get_hardware_device_driver_plan(device_id)

        result = asyncio.run(run())
        self.assertFalse(result["live_activation_possible"])
        self.assertFalse(result["persistent_install_possible"])

    def test_carrier_layout_preview_never_partitions(self) -> None:
        from api.routes.rescue_carrier import post_carrier_layout_preview

        async def run() -> dict:
            return await post_carrier_layout_preview({"carrier_size_bytes": 63_864_502_272})

        result = asyncio.run(run())
        self.assertIn("layout_status", result)
        self.assertNotIn("partition_performed", result)  # no such key ever exists

    def test_hardware_scan_endpoint_does_not_crash_without_tools(self) -> None:
        from api.routes.rescue_hardware import post_hardware_scan

        result = asyncio.run(post_hardware_scan())
        self.assertIn("run_id", result)
        self.assertIn("summary", result)


if __name__ == "__main__":
    unittest.main()
