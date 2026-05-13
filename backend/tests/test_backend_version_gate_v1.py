from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.versioning import api_version_error_code  # noqa: E402

try:
    from fastapi.testclient import TestClient

    from app import app as fastapi_app

    _HAS_TC = True
except Exception:  # noqa: BLE001
    TestClient = None  # type: ignore[misc, assignment]
    fastapi_app = None
    _HAS_TC = False


class BackendVersionGateV1Tests(unittest.TestCase):
    def test_api_version_error_code_value_error(self) -> None:
        self.assertEqual(
            api_version_error_code(ValueError("version_source_of_truth must be true")),
            "backend.version_config_invalid",
        )

    def test_api_version_error_code_json(self) -> None:
        import json

        self.assertEqual(
            api_version_error_code(json.JSONDecodeError("msg", "doc", 0)),
            "backend.version_config_invalid",
        )

    def test_api_version_error_code_other(self) -> None:
        self.assertEqual(api_version_error_code(RuntimeError("x")), "backend.update_required")

    @unittest.skipUnless(_HAS_TC, "FastAPI TestClient oder app nicht verfügbar")
    def test_api_version_success_has_gate_fields(self) -> None:
        c = TestClient(fastapi_app, base_url="http://localhost")
        r = c.get("/api/version")
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        self.assertEqual(data.get("status"), "success")
        for key in (
            "project_version",
            "release_stage",
            "version_track",
            "version_source_of_truth",
            "install_profile",
            "app_edition",
            "backend_runtime_path",
        ):
            self.assertIn(key, data, msg=f"missing {key}")

    @unittest.skipUnless(_HAS_TC, "FastAPI TestClient oder app nicht verfügbar")
    def test_api_version_503_on_invalid_version_config(self) -> None:
        c = TestClient(fastapi_app, base_url="http://localhost")
        with patch(
            "core.versioning.load_project_version",
            side_effect=ValueError("version_source_of_truth must be true"),
        ):
            r = c.get("/api/version")
        self.assertEqual(r.status_code, 503)
        body = r.json()
        self.assertEqual(body.get("code"), "backend.version_config_invalid")
        self.assertTrue(body.get("blocked_update_required"))

    def test_version_gate_script_exists(self) -> None:
        root = _backend.parent
        script = root / "scripts" / "check-backend-version-gate.sh"
        self.assertTrue(script.is_file(), msg=str(script))

    def test_cursor_rules_mention_gate_script(self) -> None:
        rules = _backend.parent / "docs" / "developer" / "CURSOR_WORK_RULES.md"
        text = rules.read_text(encoding="utf-8")
        self.assertIn("check-backend-version-gate.sh", text)
        self.assertIn("Backend-Version-Gate", text)


if __name__ == "__main__":
    unittest.main()
