"""Phase R.3: rescue_telemetry_spool contract tests."""

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


class TestRescueTelemetrySpoolR3(unittest.TestCase):
    def test_redacts_password(self) -> None:
        import core.rescue_telemetry_spool as sp

        red = sp._redact_payload({"password": "secret123", "boot_id": "abc"})
        self.assertNotEqual(red["password"], "secret123")
        self.assertEqual(red["boot_id"], "abc")

    def test_write_and_mark_sent(self) -> None:
        import core.rescue_telemetry_spool as sp

        with tempfile.TemporaryDirectory() as tmp:
            spool = Path(tmp) / "telemetry" / "spool"
            with mock.patch.object(sp, "_spool_dir", return_value=spool):
                w = sp.write_telemetry_event({"event": "test"}, event_id="evt1")
                self.assertEqual(w["status"], "ok")
                pending = sp.list_pending_telemetry_events()
                self.assertEqual(len(pending), 1)
                m = sp.mark_telemetry_event_sent("evt1", http_status=200)
                self.assertEqual(m["status"], "ok")
                pending2 = sp.list_pending_telemetry_events()
                self.assertEqual(len(pending2), 0)


if __name__ == "__main__":
    unittest.main()
