"""Phase R.3: rescue_persistence contract tests."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


class TestRescuePersistenceR3(unittest.TestCase):
    def test_diagnostics_has_version(self) -> None:
        import core.rescue_persistence as rp

        diag = rp.build_rescue_persistence_diagnostics()
        self.assertEqual(diag["persistence_version"], 4)
        self.assertIn("detect_rescue_stick_mount", diag["public_functions"])

    def test_detect_fallback_when_no_mounts(self) -> None:
        import core.rescue_persistence as rp

        with mock.patch.object(rp, "discover_findmnt_mounts_flat", return_value=[]):
            det = rp.detect_rescue_stick_mount()
        self.assertTrue(det["fallback"])
        self.assertIn("RAM", det.get("warning") or "")

    def test_write_json_uses_ram_fallback(self) -> None:
        import core.rescue_persistence as rp

        with tempfile.TemporaryDirectory() as tmp:
            with (
                mock.patch.object(rp, "detect_rescue_stick_mount", return_value={"writable_root": tmp, "fallback": True, "warning": "test"}),
                mock.patch.object(rp, "ensure_rescue_evidence_tree", return_value={"evidence_root": tmp, "fallback": True, "tree_ready": True}),
            ):
                result = rp.write_rescue_json_evidence("boot", "test.json", {"ok": True})
            path = Path(result["path"])
            self.assertTrue(path.is_file())
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["payload"]["ok"], True)

    def test_invalid_filename_rejected(self) -> None:
        import core.rescue_persistence as rp

        with self.assertRaises(ValueError):
            rp.write_rescue_json_evidence("boot", "../escape.json", {})


if __name__ == "__main__":
    unittest.main()
