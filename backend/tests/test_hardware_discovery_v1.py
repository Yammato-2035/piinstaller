"""Phase G.9: Hardware Discovery Core contract tests."""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path
from unittest import mock

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

DISCOVERY_PATH = _BACKEND / "core" / "hardware_discovery.py"

PUBLIC_FUNCTIONS = (
    "discover_cpu_info",
    "discover_memory_info",
    "discover_mainboard_info",
    "discover_pci_info",
    "discover_sensor_info",
    "discover_raspberry_pi_info",
    "build_hardware_discovery_diagnostics",
)


class TestHardwareDiscoveryV1(unittest.TestCase):
    def test_discovery_module_has_version_and_public_api(self) -> None:
        import core.hardware_discovery as discovery

        self.assertEqual(discovery.HARDWARE_DISCOVERY_VERSION, 1)
        for name in PUBLIC_FUNCTIONS:
            self.assertTrue(hasattr(discovery, name), f"missing {name}")
            self.assertTrue(callable(getattr(discovery, name)))

    def test_discovery_ast_has_no_app_import(self) -> None:
        tree = ast.parse(DISCOVERY_PATH.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotEqual(alias.name, "app")
            if isinstance(node, ast.ImportFrom) and node.module:
                self.assertFalse(node.module == "app" or node.module.startswith("app."))

    def test_discover_cpu_info_shape(self) -> None:
        import core.hardware_discovery as discovery

        with (
            mock.patch.object(discovery, "get_cpu_name", return_value="Test CPU"),
            mock.patch.object(discovery, "get_cpu_summary", return_value={"cores": 4, "threads": 8}),
            mock.patch.object(discovery, "get_cpu_temp", return_value=55.0),
            mock.patch.object(discovery, "get_fan_speed", return_value=1200),
            mock.patch.object(discovery, "get_per_core_usage", return_value=([10.0, 20.0], 2)),
        ):
            out = discovery.discover_cpu_info(per_cpu_percent=[10.0, 20.0, 30.0, 40.0])
        self.assertEqual(out["name"], "Test CPU")
        self.assertEqual(out["summary"]["cores"], 4)
        self.assertEqual(out["temperature"], 55.0)
        self.assertEqual(out["physical_cores"], 2)

    def test_discover_pci_info_shape(self) -> None:
        import core.hardware_discovery as discovery

        fake_pci = [{"address": "00:00.0", "description": "VGA", "driver": "amdgpu"}]
        fake_gpus = [{"name": "AMD GPU", "gpu_type": "discrete"}]
        with (
            mock.patch.object(discovery, "_get_pci_with_drivers", return_value=fake_pci),
            mock.patch.object(discovery, "_get_gpus_for_system_info", return_value=fake_gpus),
        ):
            out = discovery.discover_pci_info()
        self.assertEqual(out["pci_list"], fake_pci)
        self.assertEqual(out["gpus"], fake_gpus)
        self.assertTrue(callable(out["clean_gpu_description"]))

    def test_discover_sensor_info_shape(self) -> None:
        import core.hardware_discovery as discovery

        with (
            mock.patch.object(discovery, "get_all_thermal_sensors", return_value=[{"name": "cpu", "temperature": 40.0}]),
            mock.patch.object(discovery, "get_all_disks", return_value=[]),
            mock.patch.object(discovery, "get_all_fans", return_value=[]),
            mock.patch.object(discovery, "get_all_displays", return_value=[]),
        ):
            out = discovery.discover_sensor_info()
        self.assertEqual(len(out["sensors"]), 1)
        self.assertIn("disks", out)

    def test_diagnostics_present(self) -> None:
        import core.hardware_discovery as discovery

        diag = discovery.build_hardware_discovery_diagnostics()
        self.assertEqual(diag["discovery_version"], 1)
        self.assertTrue(diag["no_app_import_in_facade"])
        for fn in PUBLIC_FUNCTIONS:
            self.assertIn(fn, diag["public_functions"])


if __name__ == "__main__":
    unittest.main()
