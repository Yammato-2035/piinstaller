"""Phase G.6: System Info Facade contract tests."""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path
from unittest import mock

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

FACADE_PATH = _BACKEND / "core" / "system_info_facade.py"

PUBLIC_FUNCTIONS = (
    "build_system_info",
    "build_system_info_sections",
    "build_hardware_section",
    "build_runtime_section",
    "build_network_section",
    "build_system_info_diagnostics",
)

LIGHT_RESPONSE_KEYS = frozenset(
    {
        "os",
        "cpu",
        "memory",
        "disk",
        "platform",
        "uptime",
        "cpu_name",
        "cpu_summary",
        "app_edition",
    }
)

FULL_EXTRA_KEYS = frozenset(
    {
        "is_raspberry_pi",
        "device_type",
        "hardware",
        "motherboard",
        "ram_info",
        "manufacturer_driver_tip",
        "sensors",
        "disks",
        "fans",
        "displays",
        "drivers",
        "network",
    }
)


class TestSystemInfoFacadeV1(unittest.TestCase):
    def test_facade_module_has_version_and_public_api(self) -> None:
        import core.system_info_facade as facade

        self.assertEqual(facade.SYSTEM_INFO_FACADE_VERSION, 1)
        for name in PUBLIC_FUNCTIONS:
            self.assertTrue(hasattr(facade, name), f"missing {name}")
            self.assertTrue(callable(getattr(facade, name)))

    def test_facade_source_has_no_direct_network_discovery(self) -> None:
        tree = ast.parse(FACADE_PATH.read_text(encoding="utf-8"))
        banned = {"get_network_info", "_demo_network", "discover_network_info"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in banned:
                self.fail(f"banned symbol in facade: {node.id}")

    def test_facade_uses_network_info_facade(self) -> None:
        text = FACADE_PATH.read_text(encoding="utf-8")
        self.assertIn("network_info_facade", text)
        self.assertIn("build_network_info", text)
        self.assertIn("build_demo_network_info", text)
        self.assertIn("build_section_status", text)

    def test_build_network_section_delegates_to_network_facade(self) -> None:
        import core.system_info_facade as facade

        fake = {"ips": ["192.168.1.10"], "hostname": "host"}
        with mock.patch.object(facade, "build_network_info", return_value=fake) as build_net:
            out = facade.build_network_section(use_demo=False)
        build_net.assert_called_once_with()
        self.assertEqual(out, fake)

    def test_facade_uses_hardware_discovery(self) -> None:
        text = FACADE_PATH.read_text(encoding="utf-8")
        self.assertIn("hardware_discovery", text)
        self.assertIn("discover_cpu_info", text)
        self.assertNotIn("import app", text)
        self.assertNotIn("_legacy_", text)

    def test_build_system_info_light_shape(self) -> None:
        import contextlib
        import core.system_info_facade as facade

        fake_mem = mock.Mock(total=8, available=4, percent=50.0)
        fake_disk = mock.Mock(total=100, used=40, free=60, percent=40.0)
        patches = [
            mock.patch.object(facade.psutil, "cpu_percent", return_value=[10.0, 20.0]),
            mock.patch.object(facade.psutil, "virtual_memory", return_value=fake_mem),
            mock.patch.object(facade.psutil, "disk_usage", return_value=fake_disk),
            mock.patch.object(facade.psutil, "disk_partitions", return_value=[]),
            mock.patch.object(facade.psutil, "cpu_count", return_value=2),
            mock.patch.object(
                facade,
                "discover_cpu_info",
                return_value={"name": "Test CPU", "summary": {"cores": 2, "threads": 4}},
            ),
            mock.patch("builtins.open", mock.mock_open(read_data="3600.0 0\n")),
        ]
        with contextlib.ExitStack() as stack:
            for patcher in patches:
                stack.enter_context(patcher)
            out = facade.build_system_info(light=True, use_demo=False)
        self.assertTrue(LIGHT_RESPONSE_KEYS.issubset(set(out.keys())))
        self.assertNotIn("network", out)
        self.assertEqual(out["cpu"]["usage"], 15.0)

    def test_build_system_info_full_includes_network_via_facade(self) -> None:
        import contextlib
        import core.system_info_facade as facade

        fake_network = {"ips": ["10.0.0.2"], "hostname": "pi"}
        fake_mem = mock.Mock(total=8, available=4, percent=50.0)
        fake_disk = mock.Mock(total=100, used=40, free=60, percent=40.0)
        cpu_probe = {
            "name": "CPU",
            "summary": {"cores": 1, "threads": 1},
            "temperature": 42.0,
            "fan_speed": None,
            "per_core_usage": [],
            "physical_cores": 1,
        }
        patches = [
            mock.patch.object(facade.psutil, "cpu_percent", return_value=[5.0]),
            mock.patch.object(facade.psutil, "virtual_memory", return_value=fake_mem),
            mock.patch.object(facade.psutil, "disk_usage", return_value=fake_disk),
            mock.patch.object(facade.psutil, "disk_partitions", return_value=[]),
            mock.patch.object(facade.psutil, "cpu_count", return_value=1),
            mock.patch.object(facade, "discover_cpu_info", return_value=cpu_probe),
            mock.patch.object(facade, "discover_raspberry_pi_info", return_value={"is_raspberry_pi": False, "hardware": {"cpus": [], "gpus": []}}),
            mock.patch.object(facade, "discover_pci_info", return_value={"pci_list": [], "gpus": [], "clean_gpu_description": lambda d: d}),
            mock.patch.object(facade, "discover_mainboard_info", return_value={}),
            mock.patch.object(facade, "discover_memory_info", return_value={"ram_info": []}),
            mock.patch.object(facade, "discover_sensor_info", return_value={"sensors": [], "disks": [], "fans": [], "displays": []}),
            mock.patch.object(facade, "run_command", return_value={"success": True, "stdout": "6.1.0\n"}),
            mock.patch("builtins.open", mock.mock_open(read_data="3600.0 0\n")),
            mock.patch.object(Path, "exists", return_value=False),
        ]
        with contextlib.ExitStack() as stack:
            net_section = stack.enter_context(
                mock.patch.object(facade, "build_network_section", return_value=fake_network)
            )
            for patcher in patches:
                stack.enter_context(patcher)
            out = facade.build_system_info(light=False, use_demo=False)
        net_section.assert_called_once_with(use_demo=False)
        self.assertEqual(out["network"], fake_network)
        self.assertTrue(FULL_EXTRA_KEYS.issubset(set(out.keys())))

    def test_section_failure_isolated(self) -> None:
        import core.system_info_facade as facade

        with mock.patch.object(facade, "build_runtime_section", side_effect=RuntimeError("boom")):
            sections = facade.build_system_info_sections(light=True)
        runtime = next(s for s in sections["sections"] if s["section_id"] == "runtime")
        self.assertEqual(runtime["status"], "unavailable")
        self.assertTrue(runtime["errors"])

    def test_diagnostics_present(self) -> None:
        import core.system_info_facade as facade

        diag = facade.build_system_info_diagnostics()
        self.assertEqual(diag["facade_version"], 1)
        self.assertTrue(diag["network_via_network_info_facade"])
        self.assertTrue(diag.get("hardware_via_hardware_discovery"))
        self.assertIn("GET /api/system-info", diag["routes_migrated_to_facade"])
        for fn in PUBLIC_FUNCTIONS:
            self.assertIn(fn, diag["public_functions"])


if __name__ == "__main__":
    unittest.main()
