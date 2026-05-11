import json
import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.diagnostics.models import SystemProfile


class TestHwProfilesV1(unittest.TestCase):
    def _load(self, name: str) -> SystemProfile:
        root = Path(__file__).resolve().parents[2]
        data = json.loads((root / "data/diagnostics/profiles" / name).read_text(encoding="utf-8"))
        return SystemProfile(**data)

    def test_laptop_profile_exists(self):
        p = self._load("profile-linux-laptop-nvme-host.json")
        self.assertEqual(p.platform_class, "linux_laptop")
        self.assertGreaterEqual(p.core_count, 1)

    def test_usb_sd_sizes(self):
        usb = self._load("profile-media-usb32-stick-64gb.json")
        sd = self._load("profile-media-sdcard-64gb.json")
        self.assertAlmostEqual(usb.storage_devices[0].size_gb, 64)
        self.assertAlmostEqual(sd.storage_devices[0].size_gb, 64)
        self.assertTrue(usb.storage_devices[0].removable)
        self.assertTrue(sd.storage_devices[0].removable)


if __name__ == "__main__":
    unittest.main()
