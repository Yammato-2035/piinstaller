"""Update endpoint must never launch a terminal/apt; manual-only response."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

try:
    from fastapi.testclient import TestClient

    from app import app as fastapi_app

    _HAS_TC = True
except Exception:  # noqa: BLE001
    TestClient = None  # type: ignore[misc, assignment]
    fastapi_app = None
    _HAS_TC = False


class UpdateButtonManualOnlyTests(unittest.TestCase):
    @unittest.skipUnless(_HAS_TC, "FastAPI TestClient nicht verfuegbar")
    def test_run_update_endpoint_returns_manual_required(self) -> None:
        c = TestClient(fastapi_app, base_url="http://localhost")
        with (
            patch("app.subprocess.Popen") as popen_mock,
            patch("app.subprocess.run") as run_mock,
        ):
            r = c.post("/api/system/run-update-in-terminal")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body.get("status"), "manual_required")
        self.assertEqual(body.get("code"), "updates.manual_terminal_required")
        self.assertEqual(body.get("commands"), ["sudo apt update", "sudo apt upgrade"])
        self.assertTrue(body.get("blocked_auto_execution"))
        self.assertIn("BR-001", str(body.get("br001_warning", "")))
        popen_mock.assert_not_called()
        run_mock.assert_not_called()

    @unittest.skipUnless(_HAS_TC, "FastAPI TestClient nicht verfuegbar")
    def test_run_update_no_open_terminal_helper_call(self) -> None:
        c = TestClient(fastapi_app, base_url="http://localhost")
        with patch("app._open_terminal_with_command") as helper:
            r = c.post("/api/system/run-update-in-terminal")
        self.assertEqual(r.status_code, 200)
        helper.assert_not_called()


if __name__ == "__main__":
    unittest.main()
