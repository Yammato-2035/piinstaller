"""Unit tests for rescue live telemetry shell/python scripts (workspace copy)."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
IMAGE_DIR = REPO_ROOT / "scripts" / "rescue-live" / "image"


def _load_payload_builder():
    path = IMAGE_DIR / "setuphelfer-rescue-telemetry-build-payload.py"
    spec = importlib.util.spec_from_file_location("rescue_payload_builder", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class RescueLiveTelemetryScriptTests(unittest.TestCase):
    def test_telemetry_push_bash_syntax(self) -> None:
        script = IMAGE_DIR / "setuphelfer-rescue-telemetry-push"
        proc = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_telemetry_payload_builder_py_compile(self) -> None:
        script = IMAGE_DIR / "setuphelfer-rescue-telemetry-build-payload.py"
        proc = subprocess.run([sys.executable, "-m", "py_compile", str(script)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_payload_hash_matches_body(self) -> None:
        mod = _load_payload_builder()
        with tempfile.TemporaryDirectory() as td:
            state = Path(td)
            (state / "media-check.json").write_text('{"live_media_runtime_stable": true}', encoding="utf-8")
            (state / "network-onboarding.json").write_text('{"wifi_connected": true}', encoding="utf-8")
            payload = mod.build_payload(state)
        stored_hash = payload["payload_hash_sha256"]
        bare = dict(payload)
        bare.pop("payload_hash_sha256")
        expected = hashlib.sha256(
            json.dumps(bare, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        self.assertEqual(stored_hash, expected)

    def test_secret_redaction(self) -> None:
        mod = _load_payload_builder()
        redacted = mod.redact_secrets("wlan0: password=secret123\nok line")
        self.assertIn("[REDACTED]", redacted)
        self.assertNotIn("secret123", redacted)

    def test_lsblk_json_no_syntax_error(self) -> None:
        mod = _load_payload_builder()
        with tempfile.TemporaryDirectory() as td:
            state = Path(td)
            payload = mod.build_payload(state)
        self.assertIn("lsblk", payload["hardware"])
        self.assertIsInstance(payload["hardware"]["lsblk"], (dict, list))

    def test_network_onboarding_bash_syntax(self) -> None:
        script = IMAGE_DIR / "setuphelfer-rescue-network-onboarding"
        proc = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_boot_menu_hook_branding_markers(self) -> None:
        hook = REPO_ROOT / "scripts" / "rescue-live" / "prepare-controlled-live-build-tree.sh"
        text = hook.read_text(encoding="utf-8")
        self.assertIn("Setuphelfer Rettung starten", text)
        self.assertIn("MSI/NVIDIA-Kompatibilitaetsmodus", text)
        self.assertIn("patch_grub", text)


if __name__ == "__main__":
    unittest.main()
