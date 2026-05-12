"""
Integration-Tests: Fehlerfälle (401 ohne Session, 404 unbekanntes Modul, 403 viewer Aktion).
Lauf: cd backend && python -m unittest tests.test_remote_errors -v
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
    from storage.db import init_remote_db, hash_token
    init_remote_db(None)
    from app import app
    _HAS_TESTCLIENT = True
except (ImportError, Exception):
    _HAS_TESTCLIENT = False
    TestClient = None
    app = None
    storage_db = None
    hash_token = None


def _now_iso():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _future_iso(seconds=3600):
    from datetime import datetime, timezone, timedelta
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat()


@unittest.skipUnless(_HAS_TESTCLIENT, "TestClient/httpx oder app nicht verfügbar")
class TestRemoteErrors(unittest.TestCase):
    def setUp(self):
        if storage_db is not None:
            storage_db._remote_db_path = Path(_remote_test_db)  # noqa: SLF001
        # Host muss zu TrustedHostMiddleware passen (localhost statt Default testserver)
        self.client = TestClient(app, base_url="http://localhost")
        app.state.app_settings = {"remote": {"REMOTE_FEATURE_ENABLED": True}}
        app.state.device_id = "test-device"

    def test_modules_without_session_401(self):
        r = self.client.get("/api/modules")
        self.assertEqual(r.status_code, 401)

    def test_module_state_unknown_404(self):
        session_token = self._create_viewer_session()
        r = self.client.get(
            "/api/modules/unknown-module-id/state",
            headers={"Authorization": f"Bearer {session_token}"},
        )
        self.assertEqual(r.status_code, 404)

    def test_action_as_viewer_403(self):
        session_token = self._create_viewer_session()
        r = self.client.post(
            "/api/modules/sabrina-tuner/actions/set_volume",
            headers={"Authorization": f"Bearer {session_token}"},
            json={"payload": {"value": 50}},
        )
        self.assertEqual(r.status_code, 403)

    def _create_viewer_session(self):
        conn = storage_db.get_connection()
        try:
            import uuid
            import secrets
            device_id = "dev-" + uuid.uuid4().hex[:8]
            profile_id = "prof-" + uuid.uuid4().hex[:8]
            session_id = "sess-" + uuid.uuid4().hex[:8]
            token = secrets.token_urlsafe(16)
            token_hash = hash_token(token)
            now = _now_iso()
            exp = _future_iso()
            conn.execute(
                "INSERT INTO remote_device_profiles (id, device_id, name, role, created_at, updated_at) VALUES (?,?,?,?,?,?)",
                (profile_id, device_id, "Test", "viewer", now, now),
            )
            conn.execute(
                "INSERT INTO sessions (id, session_token_hash, device_id, created_at, expires_at, refreshed_at) VALUES (?,?,?,?,?,?)",
                (session_id, token_hash, device_id, now, exp, None),
            )
            conn.commit()
            return token
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
