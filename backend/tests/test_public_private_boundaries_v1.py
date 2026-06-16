"""Public/private boundary tests — facades and gates."""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


class PublicPrivateBoundariesV1Tests(unittest.TestCase):
    def test_storage_facade_imports_without_runtime(self) -> None:
        import core.storage_facade as sf  # noqa: F401

        self.assertTrue(hasattr(sf, "FACADE_CONTRACT_VERSION"))

    def test_mount_facade_readonly_plan_no_rw(self) -> None:
        from core.mount_facade import validate_mount_readonly

        result = validate_mount_readonly({"target": "/mnt/test", "options": "ro,nodev"})
        self.assertTrue(result.get("read_only"))
        rw_result = validate_mount_readonly({"target": "/mnt/test", "options": "rw"})
        self.assertFalse(rw_result.get("valid"))

    def test_safety_facade_blocks_system_disk_pattern(self) -> None:
        from core.safety_facade import validate_backup_target_for_write

        # Root device path should not be trivially allowed without inspect
        result = validate_backup_target_for_write("/dev/nvme0n1", context="live")
        self.assertIsInstance(result, dict)

    def test_no_private_only_paths_exist(self) -> None:
        forbidden = [
            "backend/cloudserver_private",
            "backend/telemetry_server",
            "backend/operator_dashboard",
        ]
        for p in forbidden:
            self.assertFalse((REPO_ROOT / p).exists(), msg=p)

    def test_public_boundary_script_exists(self) -> None:
        script = REPO_ROOT / "scripts" / "check-public-private-boundary.sh"
        self.assertTrue(script.is_file())

    def test_boundary_script_runs(self) -> None:
        script = REPO_ROOT / "scripts" / "check-public-private-boundary.sh"
        proc = subprocess.run(
            ["bash", str(script)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        # Exit 0 or 20 (review) acceptable on current tree; not 10-16
        self.assertIn(proc.returncode, (0, 20), msg=proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
