"""PI-RS-E2E-LIVE-001D5 payload version tests (1.10.0.23 — SABRENT destructive E2E)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from core.rescue_payload_e2e_live_001d_content import verify_rescue_payload_e2e_live_001d_content
from core.rescue_payload_version import (
    load_rescue_payload_version_config,
    previous_rescue_payload_version,
    rescue_payload_version,
)


class E2ELive001D5PayloadVersionTests(unittest.TestCase):
    def test_rescue_payload_version_is_1_10_0_23(self) -> None:
        self.assertEqual(rescue_payload_version(), "1.10.0.23")

    def test_previous_version_documented(self) -> None:
        self.assertEqual(previous_rescue_payload_version(), "1.10.0.22")

    def test_config_file_present(self) -> None:
        path = Path(__file__).resolve().parents[2] / "config" / "rescue_payload_version.json"
        self.assertTrue(path.is_file())
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["rescue_payload_version"], "1.10.0.23")

    def test_load_config_cached(self) -> None:
        load_rescue_payload_version_config.cache_clear()
        cfg = load_rescue_payload_version_config()
        self.assertEqual(cfg["rescue_payload_version"], "1.10.0.23")

    def test_e2e_content_artifact_when_present(self) -> None:
        artifact = (
            Path(__file__).resolve().parents[2]
            / "build"
            / "rescue"
            / "filesystem.squashfs.repacked-1.10.0.23"
        )
        if not artifact.is_file():
            self.skipTest(f"squashfs not built yet: {artifact}")
        result = verify_rescue_payload_e2e_live_001d_content(artifact)
        self.assertTrue(result["content_ok"], result)
        self.assertTrue(result["secrets_absent"], result)
        self.assertTrue(result.get("unattended_service_present"), result)
        self.assertTrue(result.get("unattended_service_unit_present"), result)


if __name__ == "__main__":
    unittest.main()
