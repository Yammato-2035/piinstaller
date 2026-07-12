"""PI-RS-PAYLOAD-TELEMETRY-001 no-secrets tests."""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


class PayloadTelemetry001NoSecretsTests(unittest.TestCase):
    def test_check_script_passes_on_workspace(self) -> None:
        root = Path(__file__).resolve().parents[2]
        script = root / "scripts" / "check-rescue-payload-no-secrets.sh"
        self.assertTrue(script.is_file())
        proc = subprocess.run([str(script)], cwd=root, capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_squashfs_listing_has_no_token_filename(self) -> None:
        root = Path(__file__).resolve().parents[2]
        squashfs = root / "build" / "rescue" / "filesystem.squashfs.repacked-1.10.0.15"
        if not squashfs.is_file():
            self.skipTest("squashfs not built yet")
        proc = subprocess.run(
            ["unsquashfs", "-ll", str(squashfs)],
            capture_output=True,
            text=True,
            check=False,
            timeout=180,
        )
        blob = proc.stdout + proc.stderr
        self.assertNotIn("telemetry-lab-token", blob)
        self.assertNotIn("telemetry-lab-hmac-key", blob)


if __name__ == "__main__":
    unittest.main()
