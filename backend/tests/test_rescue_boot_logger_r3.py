"""Phase R.3: rescue_boot_logger contract tests."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


class TestRescueBootLoggerR3(unittest.TestCase):
    def test_collect_kernel_cmdline_flags(self) -> None:
        import core.rescue_boot_logger as bl

        with mock.patch.object(bl, "_read_text", return_value="boot=live setuphelfer_rescue=1 setuphelfer_start_assistant=1"):
            cmd = bl.collect_kernel_cmdline()
        self.assertTrue(cmd["flags"]["setuphelfer_rescue"])
        self.assertTrue(cmd["flags"]["boot_live"])

    def test_write_boot_bundle(self) -> None:
        import core.rescue_boot_logger as bl

        with tempfile.TemporaryDirectory() as tmp:
            with (
                mock.patch.object(bl, "write_rescue_json_evidence", return_value={"path": f"{tmp}/boot.json", "status": "ok"}),
                mock.patch.object(bl, "write_rescue_text_evidence", return_value={"path": f"{tmp}/boot.txt", "status": "ok"}),
                mock.patch.object(bl, "_collect_journal_snippets", return_value=[]),
            ):
                result = bl.write_boot_evidence_bundle()
        self.assertEqual(result["status"], "ok")
        self.assertIn("boot", result["bundle"])


if __name__ == "__main__":
    unittest.main()
