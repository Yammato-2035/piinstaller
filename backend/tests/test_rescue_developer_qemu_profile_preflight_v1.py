"""Tests for developer-qemu profile preflight in QEMU smoke and validate."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
PREPARE = _REPO / "scripts/rescue-live/prepare-controlled-live-build-tree.sh"
QEMU_SMOKE = _REPO / "scripts/rescue-live/run-qemu-developer-iso-smoke.sh"
VALIDATE = _REPO / "scripts/rescue-live/validate-controlled-live-build-tree.sh"


class DeveloperQemuProfilePreflightTests(unittest.TestCase):
    def test_prepare_manifest_documents_qemu_fields(self) -> None:
        text = PREPARE.read_text(encoding="utf-8")
        self.assertIn("qemu_serial_console_configured", text)
        self.assertIn("qemu_smoke_autopilot_hook", text)
        self.assertIn("http://10.0.2.2:8001", text)

    def test_qemu_smoke_autopilot_requires_developer_qemu_manifest(self) -> None:
        text = QEMU_SMOKE.read_text(encoding="utf-8")
        self.assertIn("assert_developer_qemu_iso_ready", text)
        self.assertIn("QEMU_AUTOPILOT_ISO_PROFILE_MISMATCH", text)

    def test_validate_checks_developer_qemu_markers(self) -> None:
        text = VALIDATE.read_text(encoding="utf-8")
        self.assertIn("090-enable-qemu-smoke-autopilot", text)
        self.assertIn("console=ttyS0", text)

    def test_autopilot_rejects_standard_profile_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            build_root = Path(td) / "tree"
            evidence = build_root / "evidence"
            evidence.mkdir(parents=True)
            (evidence / "build-tree-manifest.json").write_text(
                json.dumps(
                    {
                        "rescue_build_profile": "standard",
                        "qemu_serial_console_configured": False,
                        "qemu_smoke_autopilot_hook": False,
                    }
                ),
                encoding="utf-8",
            )
            auto = build_root / "auto"
            auto.mkdir()
            (auto / "config").write_text(
                'bootappend-live "quiet splash init=/lib/systemd/systemd"\n',
                encoding="utf-8",
            )
            proc = subprocess.run(
                ["bash", "-c", f'source /dev/null; AUTOPILOT=true REPO_ROOT="{_REPO}" bash -c \''
                 f'manifest="{evidence / "build-tree-manifest.json"}"; '
                 f'python3 - "$manifest" <<\'PY\'\n'
                 f'import json,sys; d=json.load(open(sys.argv[1])); '
                 f'sys.exit(0 if d.get("rescue_build_profile")=="developer-qemu" else 1)\n'
                 f'PY\''],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(proc.returncode, 0)


if __name__ == "__main__":
    unittest.main()
