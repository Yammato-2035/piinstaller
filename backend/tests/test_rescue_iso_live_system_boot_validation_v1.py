from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.rescue_vm_boot_smoke import classify_live_system_boot_logs  # noqa: E402


class RescueIsoLiveSystemBootValidationTests(unittest.TestCase):
    def test_timeout_after_bootloader_when_only_isolinux(self) -> None:
        stdout = (
            "SeaBIOS\nBooting from DVD/CD...\n"
            "ISOLINUX 6.04 ETCD Copyright (C) 1994-2015 H. Peter Anvin et al\n"
        )
        result = classify_live_system_boot_logs(
            stdout_text=stdout,
            stderr_text="terminating on signal 15 (timeout)",
            qemu_exit_code=124,
            timeout_seconds=1200,
        )
        self.assertEqual(result["classification"], "timeout_after_bootloader")
        self.assertTrue(result["bootloader_seen"])
        self.assertFalse(result["kernel_started"])

    def test_kernel_started(self) -> None:
        result = classify_live_system_boot_logs(
            stdout_text="Loading vmlinuz...\nLinux version 6.1.0",
            stderr_text="",
            qemu_exit_code=0,
            timeout_seconds=1200,
        )
        self.assertEqual(result["classification"], "kernel_started")
        self.assertTrue(result["kernel_started"])


if __name__ == "__main__":
    unittest.main()
