"""Rescue evidence spool tests."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from rescue import rescue_evidence_spool as spool  # noqa: E402


class RescueEvidenceSpoolTests(unittest.TestCase):
    def test_sanitize_redacts_password(self) -> None:
        text = spool.sanitize_rescue_log("wifi password=secret123")
        self.assertNotIn("secret123", text)
        self.assertIn("[REDACTED]", text)

    def test_write_event_best_effort_on_readonly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "ro"
            base.mkdir()
            base.chmod(0o555)
            result = spool.write_rescue_evidence_event(
                {"message": "boot ok"},
                base=base,
                category="boot",
                best_effort=True,
            )
            self.assertFalse(result["written"])
            self.assertIsNotNone(result["error"])

    def test_spool_layout_contains_required_paths(self) -> None:
        manifest = spool.build_spool_layout_manifest()
        joined = " ".join(manifest["paths"])
        self.assertIn("setuphelfer/evidence/boot", joined)
        self.assertIn("setuphelfer/profiles/machines", joined)


if __name__ == "__main__":
    unittest.main()
