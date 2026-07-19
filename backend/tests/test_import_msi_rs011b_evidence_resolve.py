"""Tests for import-msi-rs011b-evidence.sh source path resolution."""

from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO / "scripts" / "rescue" / "import-msi-rs011b-evidence.sh"


class ImportMsiRs011bEvidenceResolveTests(unittest.TestCase):
    def _resolve(self, source: Path) -> str:
        env = os.environ.copy()
        env["DRY_RESOLVE"] = "1"
        proc = subprocess.run(
            [str(_SCRIPT), str(source)],
            capture_output=True,
            text=True,
            check=False,
            env=env,
            cwd=_REPO,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        return proc.stdout.strip()

    def test_setup_logs_mount_resolves_to_msi_rs011b(self) -> None:
        with self.subTest("temp SETUP_LOGS tree"):
            import tempfile

            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                msi = root / "setuphelfer" / "evidence" / "msi-rs011b"
                msi.mkdir(parents=True)
                (msi / "lab-auto-result.json").write_text("{}", encoding="utf-8")
                self.assertEqual(self._resolve(root), str(msi))

    def test_direct_msi_rs011b_path(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            msi = Path(tmp) / "msi-rs011b"
            msi.mkdir()
            (msi / "api-version.json").write_text("{}", encoding="utf-8")
            self.assertEqual(self._resolve(msi), str(msi))

    def test_missing_evidence_dir_fails(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["DRY_RESOLVE"] = "1"
            proc = subprocess.run(
                [_SCRIPT, tmp],
                capture_output=True,
                text=True,
                check=False,
                env=env,
                cwd=_REPO,
            )
            self.assertNotEqual(proc.returncode, 0)


if __name__ == "__main__":
    unittest.main()
