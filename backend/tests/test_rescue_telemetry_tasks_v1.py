"""Rescue telemetry controlled task pull tests."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.rescue_telemetry_tasks import (  # noqa: E402
    ALLOWED_TASK_TYPES,
    enqueue_dev_task,
    get_next_task,
    store_task_result,
    validate_task_manifest,
)

try:
    from fastapi.testclient import TestClient

    from app import app as fastapi_app

    _HAS_TC = True
except Exception:
    TestClient = None  # type: ignore[misc, assignment]
    fastapi_app = None  # type: ignore[misc, assignment]
    _HAS_TC = False


class RescueTelemetryTasksTests(unittest.TestCase):
    def test_unknown_task_rejected(self) -> None:
        ok, reason = validate_task_manifest({"task_id": "t1", "task_type": "run_shell", "expires_at": "2099-01-01T00:00:00Z"})
        self.assertFalse(ok)
        self.assertEqual(reason, "unknown_task_type")

    def test_expired_task_rejected(self) -> None:
        ok, reason = validate_task_manifest(
            {
                "task_id": "t2",
                "task_type": "collect_logs",
                "expires_at": "2020-01-01T00:00:00Z",
            }
        )
        self.assertFalse(ok)
        self.assertEqual(reason, "task_expired")

    def test_allowlisted_task_accepted(self) -> None:
        exp = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat().replace("+00:00", "Z")
        ok, reason = validate_task_manifest(
            {"task_id": "t3", "task_type": "run_media_check", "expires_at": exp, "dry_run": True}
        )
        self.assertTrue(ok)
        self.assertIsNone(reason)

    def test_forbidden_shell_key_rejected(self) -> None:
        exp = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat().replace("+00:00", "Z")
        ok, reason = validate_task_manifest(
            {"task_id": "t4", "task_type": "collect_logs", "expires_at": exp, "shell": "id"}
        )
        self.assertFalse(ok)
        self.assertEqual(reason, "forbidden_task_key")

    def test_get_next_and_store_result(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with patch("core.rescue_telemetry_tasks.tasks_storage_root", return_value=root):
                task = enqueue_dev_task("show_operator_message", boot_id="boot-abc", params={"message": "hello"})
                nxt = get_next_task(boot_id="boot-abc")
                self.assertIsNotNone(nxt)
                self.assertEqual(nxt["task_id"], task["task_id"])
                stored = store_task_result(
                    {
                        "boot_id": "boot-abc",
                        "task_id": task["task_id"],
                        "task_type": task["task_type"],
                        "result_status": "ok",
                        "result_payload": {"summary": "done"},
                        "dry_run": True,
                    }
                )
                self.assertTrue(stored.get("stored"))
                self.assertIsNone(get_next_task(boot_id="boot-abc"))


@unittest.skipUnless(_HAS_TC, "FastAPI TestClient nicht verfügbar")
class RescueTelemetryTasksHttpTests(unittest.TestCase):
    def test_tasks_next_204_when_empty(self) -> None:
        with patch("rescue_telemetry.routers.get_next_task", return_value=None):
            client = TestClient(fastapi_app, base_url="http://localhost")
            r = client.get("/api/rescue/telemetry/v1/tasks/next?boot_id=test")
            self.assertEqual(r.status_code, 204)

    def test_tasks_result_stores(self) -> None:
        with patch(
            "rescue_telemetry.routers.store_task_result",
            return_value={"stored": True, "task_id": "rtask-1"},
        ):
            client = TestClient(fastapi_app, base_url="http://localhost")
            r = client.post(
                "/api/rescue/telemetry/v1/tasks/result",
                json={"task_id": "rtask-1", "result_status": "ok", "task_type": "collect_logs"},
            )
            self.assertEqual(r.status_code, 200)
            self.assertTrue(r.json().get("stored"))


if __name__ == "__main__":
    unittest.main()
