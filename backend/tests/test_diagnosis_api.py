"""API POST /api/diagnosis/interpret — JSON-Form und Interpreter-Anbindung."""

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

try:
    from fastapi.testclient import TestClient
    from app import app

    _HAS = True
except Exception:
    _HAS = False
    TestClient = None
    app = None


@unittest.skipUnless(_HAS, "FastAPI TestClient oder app nicht verfügbar")
class TestDiagnosisApi(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app, base_url="http://localhost")

    def test_interpret_firewall_sudo(self):
        r = self.client.post(
            "/api/diagnosis/interpret",
            json={
                "area": "firewall",
                "event_type": "api_error",
                "api_status": "error",
                "message": "Sudo-Passwort erforderlich",
            },
        )
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        self.assertEqual(data["diagnosis_id"], "firewall.sudo_required")
        self.assertEqual(data["schema_version"], "1")
        self.assertIn("interpreter_version", data)

    def test_interpret_invalid_body_422(self):
        r = self.client.post("/api/diagnosis/interpret", json={})
        self.assertEqual(r.status_code, 422)

    def test_interpret_webserver_port_conflict(self):
        r = self.client.post(
            "/api/diagnosis/interpret",
            json={
                "area": "webserver",
                "event_type": "configure_failed",
                "api_status": "error",
                "message": "could not bind to :443",
            },
        )
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        self.assertEqual(data["diagnosis_id"], "webserver.port_conflict")

    def test_interpret_backup_verify_failed(self):
        r = self.client.post(
            "/api/diagnosis/interpret",
            json={
                "area": "backup_restore",
                "event_type": "verify_failed",
                "message": "archive corrupted",
                "extra": {"verify_mode": "basic"},
            },
        )
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        self.assertEqual(data["diagnosis_id"], "backup_restore.verify_failed_generic")
        self.assertEqual(data["area"], "backup_restore")


if __name__ == "__main__":
    unittest.main()
