from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.rescue_vm_boot_smoke import classify_vm_boot_smoke_logs  # noqa: E402


class RescueIsoVmBootSmokeClassificationTests(unittest.TestCase):
    def test_timeout_empty_stdout(self) -> None:
        result = classify_vm_boot_smoke_logs(
            stdout_text="",
            stderr_text="qemu-system-x86_64: terminating on signal 15 from pid 1 (timeout)",
            qemu_exit_code=124,
            timeout_seconds=120,
        )
        self.assertEqual(result["classification"], "timeout_no_boot_signal")
        self.assertTrue(result["timeout_reached"])
        self.assertFalse(result["bootloader_seen"])

    def test_bootloader_seen(self) -> None:
        result = classify_vm_boot_smoke_logs(
            stdout_text="ISOLINUX 6.04 boot:",
            stderr_text="",
            qemu_exit_code=0,
            timeout_seconds=120,
        )
        self.assertEqual(result["classification"], "bootloader_seen")
        self.assertTrue(result["bootloader_seen"])

    def test_nographic_isolinux_after_timeout(self) -> None:
        stdout = "SeaBIOS\nBooting from DVD/CD...\nISOLINUX 6.04"
        result = classify_vm_boot_smoke_logs(
            stdout_text=stdout,
            stderr_text="terminating on signal 15 (timeout)",
            qemu_exit_code=124,
            timeout_seconds=600,
        )
        self.assertEqual(result["classification"], "bootloader_seen")
        self.assertTrue(result["bios_seen"])


if __name__ == "__main__":
    unittest.main()
