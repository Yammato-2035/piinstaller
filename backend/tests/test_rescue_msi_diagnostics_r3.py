"""Phase R.3: rescue_msi_diagnostics contract tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


class TestRescueMsiDiagnosticsR3(unittest.TestCase):
    def test_msi_vendor_detection(self) -> None:
        import core.rescue_msi_diagnostics as md

        self.assertTrue(md._is_msi_vendor("Micro-Star International Co., Ltd."))
        self.assertFalse(md._is_msi_vendor("Dell Inc."))

    def test_snapshot_has_policy(self) -> None:
        import core.rescue_msi_diagnostics as md

        with (
            mock.patch.object(md, "collect_bootloader_context", return_value={"firmware_mode": "uefi"}),
            mock.patch.object(md, "_dmi_fields", return_value={"sys_vendor": "MSI", "product_name": "Test"}),
            mock.patch.object(md, "list_classified_devices", return_value=[]),
            mock.patch.object(md, "_run_capture", return_value=(1, "")),
        ):
            snap = md.collect_msi_hardware_snapshot()
        self.assertFalse(snap["policy"]["internal_writes"])
        self.assertTrue(snap["is_msi_candidate"])


if __name__ == "__main__":
    unittest.main()
