"""Deploy notifications router Phase D.9 — evaluation, no extraction when unsafe."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

_REPO = _BACKEND.parent
_SLICE_DOC = _REPO / "docs" / "evidence" / "deploy-runner" / "DEPLOY_NOTIFICATIONS_ROUTER_SLICE_D9.md"
_CANDIDATES_DOC = _REPO / "docs" / "evidence" / "deploy-runner" / "DEPLOY_NOTIFICATIONS_ROUTER_CANDIDATES_D9.md"


class DeployRoutesNotificationsV1Tests(unittest.TestCase):
    def test_no_safe_d9_notifications_slice_documented(self) -> None:
        self.assertTrue(_SLICE_DOC.is_file(), "slice evidence missing")
        self.assertTrue(_CANDIDATES_DOC.is_file(), "candidates evidence missing")
        slice_text = _SLICE_DOC.read_text(encoding="utf-8")
        self.assertIn("no_safe_d9_notifications_slice", slice_text)

    def test_routes_notifications_not_created(self) -> None:
        self.assertFalse(
            (_BACKEND / "deploy" / "routes_notifications.py").is_file(),
            "routes_notifications.py must not exist without safe slice",
        )

    def test_routes_py_no_notifications_router_include(self) -> None:
        routes_src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        self.assertNotIn("routes_notifications", routes_src)
        self.assertNotIn("deploy_notifications_router", routes_src)

    def test_routes_py_unchanged_runner_import_count(self) -> None:
        routes_src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        count = len(re.findall(r"^from deploy\.runner_", routes_src, flags=re.M))
        self.assertEqual(count, 93)

    def test_no_notification_paths_in_routes_py(self) -> None:
        routes_src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8").lower()
        for keyword in ("notification", "notify", "smtp", "send_mail", "sendmail"):
            self.assertNotIn(keyword, routes_src, msg=keyword)
