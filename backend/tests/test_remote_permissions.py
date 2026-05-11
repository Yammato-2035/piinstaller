"""
Unit-Tests: Rollenprüfung (require_roles, require_write, require_admin, role_level).
Lauf: cd backend && python -m unittest tests.test_remote_permissions -v
"""

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.auth import SessionContext
from core.permissions import (
    role_level,
    has_min_role,
    require_roles,
    can_perform_write,
    require_write,
    require_admin,
)


class TestRoleLevel(unittest.TestCase):
    def test_role_level_known(self):
        self.assertEqual(role_level("viewer"), 0)
        self.assertEqual(role_level("controller"), 1)
        self.assertEqual(role_level("admin"), 2)

    def test_role_level_unknown(self):
        self.assertEqual(role_level("unknown"), 0)


class TestHasMinRole(unittest.TestCase):
    def test_viewer_has_min_viewer(self):
        ctx = SessionContext(session_id="s", device_id="d", role="viewer")
        self.assertTrue(has_min_role(ctx, "viewer"))

    def test_viewer_has_not_min_controller(self):
        ctx = SessionContext(session_id="s", device_id="d", role="viewer")
        self.assertFalse(has_min_role(ctx, "controller"))


class TestRequireWrite(unittest.TestCase):
    def test_viewer_cannot_write(self):
        from fastapi import HTTPException
        ctx = SessionContext(session_id="s", device_id="d", role="viewer")
        with self.assertRaises(HTTPException) as cm:
            require_write(ctx)
        self.assertEqual(cm.exception.status_code, 403)

    def test_controller_can_write(self):
        ctx = SessionContext(session_id="s", device_id="d", role="controller")
        require_write(ctx)


class TestRequireAdmin(unittest.TestCase):
    def test_viewer_not_admin(self):
        from fastapi import HTTPException
        ctx = SessionContext(session_id="s", device_id="d", role="viewer")
        with self.assertRaises(HTTPException) as cm:
            require_admin(ctx)
        self.assertEqual(cm.exception.status_code, 403)

    def test_admin_ok(self):
        ctx = SessionContext(session_id="s", device_id="d", role="admin")
        require_admin(ctx)


class TestRequireRoles(unittest.TestCase):
    def test_require_roles_denied(self):
        from fastapi import HTTPException
        ctx = SessionContext(session_id="s", device_id="d", role="viewer")
        with self.assertRaises(HTTPException) as cm:
            require_roles(ctx, "admin")
        self.assertEqual(cm.exception.status_code, 403)

    def test_require_roles_allowed(self):
        ctx = SessionContext(session_id="s", device_id="d", role="controller")
        require_roles(ctx, "controller", "admin")


class TestCanPerformWrite(unittest.TestCase):
    def test_viewer_no_write(self):
        ctx = SessionContext(session_id="s", device_id="d", role="viewer")
        self.assertFalse(can_perform_write(ctx))

    def test_controller_write(self):
        ctx = SessionContext(session_id="s", device_id="d", role="controller")
        self.assertTrue(can_perform_write(ctx))


if __name__ == "__main__":
    unittest.main()
