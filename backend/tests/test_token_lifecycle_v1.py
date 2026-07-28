"""
Regressionstests für core/token_lifecycle.py (Paket 5, E-09).

Deckt ab: Access-/Refresh-Token-Ausgabe, Ablauf, Rotation und die
Reuse-Detection (Wiederverwendung eines bereits rotierten Refresh-Tokens
muss die gesamte Session revoken).

Lauf: cd backend && python -m unittest tests.test_token_lifecycle_v1 -v
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
_TEST_DB = _tmp.name
os.environ["PI_INSTALLER_REMOTE_DB"] = _TEST_DB

from storage import db as storage_db  # noqa: E402
from storage.db import get_connection, hash_token, init_remote_db  # noqa: E402
from core import token_lifecycle as tl  # noqa: E402


class TokenLifecycleV1Tests(unittest.TestCase):
    def setUp(self):
        storage_db._remote_db_path = Path(_TEST_DB)  # noqa: SLF001
        init_remote_db(None)
        conn = get_connection()
        try:
            conn.execute("DELETE FROM sessions")
            conn.commit()
        finally:
            conn.close()
        self.session_id = "sess-token-lifecycle-v1"
        conn = get_connection()
        try:
            conn.execute(
                """INSERT INTO sessions (id, session_token_hash, device_id, created_at, expires_at)
                   VALUES (?, ?, ?, datetime('now'), datetime('now', '+1 day'))""",
                (self.session_id, hash_token("legacy-placeholder"), "device-token-lifecycle-v1"),
            )
            conn.commit()
        finally:
            conn.close()

    def test_issue_token_pair_is_valid_immediately(self):
        pair = tl.issue_token_pair(self.session_id, refresh_ttl_seconds=86400)
        match = tl.validate_access_token(pair.access_token)
        self.assertIsNotNone(match)
        session_id, device_id, role = match
        self.assertEqual(session_id, self.session_id)
        self.assertEqual(device_id, "device-token-lifecycle-v1")

    def test_validate_access_token_rejects_unknown_token(self):
        tl.issue_token_pair(self.session_id, refresh_ttl_seconds=86400)
        self.assertIsNone(tl.validate_access_token("not-a-real-token"))

    def test_validate_access_token_rejects_expired(self):
        pair = tl.issue_token_pair(self.session_id, refresh_ttl_seconds=86400, access_ttl_seconds=-1)
        self.assertIsNone(tl.validate_access_token(pair.access_token))

    def test_rotate_with_refresh_token_issues_new_pair(self):
        first = tl.issue_token_pair(self.session_id, refresh_ttl_seconds=86400)
        second = tl.rotate_with_refresh_token(first.refresh_token, refresh_ttl_seconds=86400)
        self.assertIsNotNone(second)
        self.assertNotEqual(second.access_token, first.access_token)
        self.assertNotEqual(second.refresh_token, first.refresh_token)
        self.assertIsNotNone(tl.validate_access_token(second.access_token))

    def test_rotate_rejects_expired_refresh_token(self):
        first = tl.issue_token_pair(self.session_id, refresh_ttl_seconds=-1)
        self.assertIsNone(tl.rotate_with_refresh_token(first.refresh_token, refresh_ttl_seconds=86400))

    def test_rotate_rejects_unknown_refresh_token(self):
        tl.issue_token_pair(self.session_id, refresh_ttl_seconds=86400)
        self.assertIsNone(tl.rotate_with_refresh_token("not-a-real-refresh-token", refresh_ttl_seconds=86400))

    def test_reuse_of_rotated_refresh_token_revokes_session(self):
        first = tl.issue_token_pair(self.session_id, refresh_ttl_seconds=86400)
        second = tl.rotate_with_refresh_token(first.refresh_token, refresh_ttl_seconds=86400)
        self.assertIsNotNone(second)

        # Diebstahlsignal: der ALTE (bereits rotierte) Refresh-Token wird erneut vorgelegt.
        reuse_result = tl.rotate_with_refresh_token(first.refresh_token, refresh_ttl_seconds=86400)
        self.assertIsNone(reuse_result)

        # Die gesamte Session ist tot — auch der eigentlich noch gültige NEUE Token.
        self.assertIsNone(tl.validate_access_token(second.access_token))
        self.assertIsNone(tl.rotate_with_refresh_token(second.refresh_token, refresh_ttl_seconds=86400))

        conn = get_connection()
        try:
            cur = conn.execute("SELECT revoked FROM sessions WHERE id = ?", (self.session_id,))
            self.assertEqual(cur.fetchone()[0], 1)
        finally:
            conn.close()

    def test_issue_token_pair_rejects_revoked_session(self):
        conn = get_connection()
        try:
            conn.execute("UPDATE sessions SET revoked = 1 WHERE id = ?", (self.session_id,))
            conn.commit()
        finally:
            conn.close()
        with self.assertRaises(ValueError):
            tl.issue_token_pair(self.session_id, refresh_ttl_seconds=86400)


if __name__ == "__main__":
    unittest.main()
