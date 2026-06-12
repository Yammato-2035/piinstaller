"""Phase F.4: DCC facade delegation — ai_prompt stub + readonly router."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path
from unittest import mock

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

APP_PY = _BACKEND / "app.py"
READONLY_ROUTER = _BACKEND / "api" / "routes" / "dev_dashboard_readonly.py"

FACADE_READONLY_IMPORTS = (
    "build_dcc_backend_health_api",
    "build_dcc_notifications_status_api",
    "build_dcc_notifications_events_api",
    "build_dcc_evidence_index_api",
)


class TestDccStatusFacadeDelegationF4(unittest.TestCase):
    def test_ai_prompt_stub_uses_facade_not_build_dashboard_status(self) -> None:
        text = APP_PY.read_text(encoding="utf-8")
        stub_start = text.index("async def ai_prompt_generate_stub")
        stub_block = text[stub_start : stub_start + 1200]
        self.assertIn("build_dcc_cursor_meta_prompt_api", stub_block)
        self.assertNotIn("build_dashboard_status", stub_block)
        self.assertNotIn("build_prompt_findings", stub_block)
        self.assertNotIn("build_cursor_meta_prompt", stub_block)

    def test_readonly_router_uses_facade_api_helpers(self) -> None:
        text = READONLY_ROUTER.read_text(encoding="utf-8")
        for imp in FACADE_READONLY_IMPORTS:
            self.assertIn(imp, text, f"missing facade import {imp}")
        self.assertNotIn("load_backend_health_snapshot", text)
        self.assertNotIn("build_notification_summary", text)
        self.assertNotIn("list_notification_events", text)
        self.assertNotIn("dev_dashboard_core.build_evidence_index", text)

    def test_readonly_router_no_direct_core_aggregation(self) -> None:
        text = READONLY_ROUTER.read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"build_dashboard_status", text))

    def test_ai_prompt_stub_response_shape_unchanged(self) -> None:
        import core.dcc_status_facade as facade

        with (
            mock.patch.object(facade, "build_dashboard_status_body", return_value={"generated_at": "t"}),
            mock.patch("core.dev_dashboard._repo_root", return_value=Path("/tmp/repo")),
            mock.patch(
                "core.dev_dashboard_cockpit.build_prompt_findings",
                return_value=[{"id": "f1"}],
            ),
            mock.patch(
                "core.dev_dashboard_cockpit.build_cursor_meta_prompt",
                return_value={"prompt": "test-prompt", "title": "t"},
            ),
        ):
            meta = facade.build_dcc_cursor_meta_prompt_api()
            out = {
                "status": "success",
                "provider": "manual",
                "executed": False,
                "message_key": "devDashboard.aiPrompt.manualOnly",
                "prompt": meta.get("prompt"),
            }
        self.assertEqual(out["prompt"], "test-prompt")
        self.assertFalse(out["executed"])
        self.assertEqual(meta["status"], "success")

    def test_backend_health_api_returns_snapshot_shape(self) -> None:
        import core.dcc_status_facade as facade

        fake_snapshot = {"status": "ok", "stale": False, "current_health": {}}
        with mock.patch.object(
            facade,
            "build_dcc_backend_health_section",
            return_value={"data": {"snapshot": fake_snapshot}},
        ):
            out = facade.build_dcc_backend_health_api()
        self.assertEqual(out, fake_snapshot)

    def test_notifications_status_api_preserves_code_wrapper(self) -> None:
        import core.dcc_status_facade as facade

        fake_summary = {"status": "gray", "event_count": 0}
        with mock.patch.object(
            facade,
            "build_dcc_notification_section",
            return_value={"data": {"summary": fake_summary}},
        ):
            out = facade.build_dcc_notifications_status_api()
        self.assertEqual(out["code"], "DEV_DASHBOARD_NOTIFICATIONS_STATUS_OK")
        self.assertEqual(out["status"], "gray")
        self.assertEqual(out["event_count"], 0)

    def test_notifications_events_api_preserves_code_wrapper(self) -> None:
        import core.notification_state as notification_state
        import core.dcc_status_facade as facade

        with mock.patch.object(
            notification_state,
            "list_notification_events",
            return_value={"events": [], "event_count": 0},
        ):
            out = facade.build_dcc_notifications_events_api(limit=10)
        self.assertEqual(out["code"], "DEV_DASHBOARD_NOTIFICATIONS_EVENTS_OK")
        self.assertEqual(out["events"], [])

    def test_evidence_index_api_returns_legacy_index(self) -> None:
        import core.dcc_status_facade as facade

        fake_index = {"status": "success", "buckets": [], "warnings": []}
        with mock.patch.object(
            facade,
            "build_dcc_evidence_section",
            return_value={"data": {"index": fake_index}},
        ):
            out = facade.build_dcc_evidence_index_api()
        self.assertEqual(out, fake_index)

    def test_profile_gate_still_in_readonly_backend_health(self) -> None:
        text = READONLY_ROUTER.read_text(encoding="utf-8")
        self.assertIn("build_dcc_profile_block_response", text)


if __name__ == "__main__":
    unittest.main()
