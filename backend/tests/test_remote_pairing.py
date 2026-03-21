"""
Integration-Tests: Pairing create/claim, Replay-Schutz.
Verwendet TestClient und temporäre DB. Setzt app.state für Remote-Feature.
Lauf: cd backend && python -m unittest tests.test_remote_pairing -v
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
_remote_test_db = _tmp.name
os.environ["PI_INSTALLER_REMOTE_DB"] = _remote_test_db

try:
    from fastapi.testclient import TestClient
    from storage import db as storage_db
    from storage.db import init_remote_db
    init_remote_db(None)
    from app import app
    _HAS_TESTCLIENT = True
except (ImportError, Exception):
    _HAS_TESTCLIENT = False
    TestClient = None
    app = None
    storage_db = None


@unittest.skipUnless(_HAS_TESTCLIENT, "TestClient/httpx oder app nicht verfügbar")
class TestPairingCreateClaim(unittest.TestCase):
    def setUp(self):
        if storage_db is not None:
            storage_db._remote_db_path = Path(_remote_test_db)  # noqa: SLF001
        self.client = TestClient(app, base_url="http://localhost")
        app.state.app_settings = {
            "remote": {
                "REMOTE_FEATURE_ENABLED": True,
                "REMOTE_PAIRING_TTL_SECONDS": 300,
                "REMOTE_SESSION_TTL_SECONDS": 86400,
            }
        }
        app.state.device_id = "test-device-id"

    def test_create_returns_payload(self):
        r = self.client.post("/api/pairing/create", json={})
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        self.assertIn("ticket_id", data)
        self.assertIn("payload", data)
        self.assertIn("pair_token", data["payload"])
        self.assertIn("expires_at", data["payload"])

    def test_claim_success_returns_session_token(self):
        r = self.client.post("/api/pairing/create", json={})
        self.assertEqual(r.status_code, 200)
        pair_token = r.json()["payload"]["pair_token"]
        r2 = self.client.post("/api/pairing/claim", json={"pair_token": pair_token})
        self.assertEqual(r2.status_code, 200)
        data = r2.json()
        self.assertTrue(data["success"])
        self.assertIn("session_token", data)

    def test_claim_replay_returns_false(self):
        r = self.client.post("/api/pairing/create", json={})
        self.assertEqual(r.status_code, 200)
        pair_token = r.json()["payload"]["pair_token"]
        self.client.post("/api/pairing/claim", json={"pair_token": pair_token})
        r3 = self.client.post("/api/pairing/claim", json={"pair_token": pair_token})
        self.assertEqual(r3.status_code, 200)
        self.assertFalse(r3.json()["success"])
        self.assertIn("bereits verwendet", r3.json().get("message", ""))

    def test_claim_invalid_token_returns_false(self):
        r = self.client.post("/api/pairing/claim", json={"pair_token": "invalid-token"})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["success"])


if __name__ == "__main__":
    unittest.main()
