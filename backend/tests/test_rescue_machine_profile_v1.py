"""Rescue machine profile tests."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from rescue import rescue_machine_profile as profile  # noqa: E402


class RescueMachineProfileTests(unittest.TestCase):
    def test_machine_id_hides_raw_serial(self) -> None:
        p = profile.build_machine_profile(
            dmi_fields={"sys_vendor": "MSI", "product_serial": "SECRET-SERIAL-123"},
        )
        self.assertNotIn("SECRET-SERIAL", str(p))
        self.assertTrue(p["machine_id"])

    def test_profile_rejects_wifi_password(self) -> None:
        bad = {"schema_version": 1, "wifi_password": "x"}
        errors = profile.validate_machine_profile(bad)
        self.assertTrue(errors)

    def test_save_and_load_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "current.json"
            built = profile.build_machine_profile(dmi_fields={"sys_vendor": "MSI"})
            result = profile.save_machine_profile(built, path)
            self.assertTrue(result["written"])
            loaded = profile.load_machine_profile(path)
            self.assertEqual(loaded["vendor"], "MSI")


if __name__ == "__main__":
    unittest.main()
