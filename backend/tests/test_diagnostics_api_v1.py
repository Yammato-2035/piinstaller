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


@unittest.skipUnless(_HAS, "FastAPI TestClient oder app nicht verfuegbar")
class TestDiagnosticsApiV1(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app, base_url="http://localhost")

    def test_catalog_available(self):
        r = self.client.get("/api/diagnostics/catalog")
        self.assertEqual(r.status_code, 200, r.text)
        payload = r.json()
        self.assertGreaterEqual(payload.get("count", 0), 25)

    def test_analyze_returns_primary(self):
        r = self.client.post(
            "/api/diagnostics/analyze",
            json={
                "question": "Restore lief durch, Weboberflaeche startet nicht",
                "context": {"platform": "raspberry_pi", "mode": "post_restore"},
                "signals": {
                    "backend_service_active": False,
                    "frontend_service_active": True,
                    "manifest_present": True,
                    "verify_status": "ok",
                },
            },
        )
        self.assertEqual(r.status_code, 200, r.text)
        payload = r.json()
        self.assertEqual(payload["primary_diagnosis"]["id"], "UI-NO-BACKEND-015")
        self.assertIn("messages", payload)


if __name__ == "__main__":
    unittest.main()
