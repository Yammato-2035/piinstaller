from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


class RescueIsoDangerousPathValidatorTests(unittest.TestCase):
    REPO = Path(__file__).resolve().parents[2]
    VALIDATOR = REPO / "scripts/rescue-live/validate-live-build-dpkg-preflight.sh"

    def _write_minimal_tree(self, root: Path, *, etc_files: dict[str, str] | None = None) -> None:
        (root / "auto").mkdir(parents=True)
        (root / "auto/config").write_text("lb config noauto\n", encoding="utf-8")
        (root / "auto/build").write_text(
            "Use controlled gate before running lb build\n",
            encoding="utf-8",
        )
        (root / "auto/clean").write_text(
            "rm -rf .build chroot cache binary local\n",
            encoding="utf-8",
        )
        package_list = root / "config/package-lists/setuphelfer.list.chroot"
        package_list.parent.mkdir(parents=True, exist_ok=True)
        package_list.write_text("dbus\nsystemd\nsystemd-sysv\n", encoding="utf-8")
        etc_root = root / "config/includes.chroot/etc/systemd/system"
        etc_root.mkdir(parents=True, exist_ok=True)
        for name, body in (etc_files or {}).items():
            (etc_root / name).write_text(body, encoding="utf-8")

    def _run_validator(self, build_root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(self.VALIDATOR), str(build_root)],
            cwd=self.REPO,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_dev_agent_pythonpath_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "build-tree"
            self._write_minimal_tree(
                root,
                etc_files={
                    "setuphelfer-dev-agent.service": (
                        "[Service]\n"
                        "Environment=PYTHONPATH=/opt/setuphelfer-rescue\n"
                    ),
                },
            )
            proc = self._run_validator(root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("pre_chroot_ok", proc.stdout)

    def test_path_override_still_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "build-tree"
            self._write_minimal_tree(
                root,
                etc_files={
                    "evil.service": "[Service]\nEnvironment=PATH=/opt/evil\n",
                },
            )
            proc = self._run_validator(root)
            self.assertEqual(proc.returncode, 14, proc.stdout + proc.stderr)
            self.assertIn("dangerous_path_override", proc.stdout)
            self.assertIn("/opt/evil", proc.stdout)

    def test_export_path_still_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "build-tree"
            self._write_minimal_tree(root)
            hook = root / "config/hooks/normal/010-evil.hook.chroot"
            hook.parent.mkdir(parents=True, exist_ok=True)
            hook.write_text("#!/bin/bash\nexport PATH=/opt/evil\n", encoding="utf-8")
            proc = self._run_validator(root)
            self.assertEqual(proc.returncode, 14, proc.stdout + proc.stderr)
            self.assertIn("dangerous_path_override", proc.stdout)

    def test_foreign_opt_path_override_still_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "build-tree"
            self._write_minimal_tree(
                root,
                etc_files={
                    "other.service": "[Service]\nEnvironment=PATH=/opt/evil\n",
                },
            )
            proc = self._run_validator(root)
            self.assertEqual(proc.returncode, 14, proc.stdout + proc.stderr)
            self.assertIn("dangerous_path_override", proc.stdout)
            self.assertIn("/opt/evil", proc.stdout)

    def test_validator_script_syntax(self) -> None:
        proc = subprocess.run(
            ["bash", "-n", str(self.VALIDATOR)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main()
