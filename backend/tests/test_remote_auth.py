"""
Unit-Tests: Session-Validierung (validate_session_token).
Verwendet temporäre SQLite-DB.
Lauf: cd backend && python -m unittest tests.test_remote_auth -v
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

# DB-Pfad vor Import setzen
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["PI_INSTALLER_REMOTE_DB"] = _tmp.name

from storage.db import init_remote_db, get_connection, hash_token
from core.auth import validate_session_token, SessionContext


def _now_iso():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _future_iso(seconds=3600):
    from datetime import datetime, timezone, timedelta
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat()


def _past_iso(seconds=-60):
    from datetime import datetime, timezone, timedelta
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat()


class TestValidateSessionToken(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_remote_db(None)
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO remote_device_profiles (id, device_id, name, role, created_at, updated_at) VALUES (?,?,?,?,?,?)",
                ("prof1", "dev1", "Test", "viewer", _now_iso(), _now_iso()),
            )
            conn.commit()
        finally:
            conn.close()

    def test_empty_token_returns_none(self):
        self.assertIsNone(validate_session_token(""))
        self.assertIsNone(validate_session_token("   "))

    def test_invalid_token_returns_none(self):
        self.assertIsNone(validate_session_token("invalid-token"))

    def test_valid_token_returns_context(self):
        conn = get_connection()
        try:
            session_id = "sess-valid-1"
            plain = "secret-token-123"
            token_hash = hash_token(plain)
            conn.execute(
                "INSERT INTO sessions (id, session_token_hash, device_id, created_at, expires_at, refreshed_at) VALUES (?,?,?,?,?,?)",
                (session_id, token_hash, "dev1", _now_iso(), _future_iso(), None),
            )
            conn.commit()
        finally:
            conn.close()
        ctx = validate_session_token(plain)
        self.assertIsInstance(ctx, SessionContext)
        self.assertEqual(ctx.session_id, session_id)
        self.assertEqual(ctx.device_id, "dev1")
        self.assertEqual(ctx.role, "viewer")

    def test_expired_token_returns_none(self):
        conn = get_connection()
        try:
            session_id = "sess-expired-1"
            plain = "expired-token"
            token_hash = hash_token(plain)
            conn.execute(
                "INSERT INTO sessions (id, session_token_hash, device_id, created_at, expires_at, refreshed_at) VALUES (?,?,?,?,?,?)",
                (session_id, token_hash, "dev1", _now_iso(), _past_iso(), None),
            )
            conn.commit()
        finally:
            conn.close()
        self.assertIsNone(validate_session_token(plain))


if __name__ == "__main__":
    unittest.main()
