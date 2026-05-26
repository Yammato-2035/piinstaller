"""Tests for the development dashboard roadmap registry."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.dev_dashboard_roadmap import (  # noqa: E402
    ALLOWED_PROMPT_STATUSES,
    ALLOWED_STATUS_VALUES,
    export_next_prompt_text,
    load_roadmap_registry_bundle,
)

_repo = Path(__file__).resolve().parent.parent.parent


def _read_json(rel: str) -> dict:
    return json.loads((_repo / rel).read_text(encoding="utf-8"))


def _iter_statuses(roadmap: dict) -> list[str]:
    values: list[str] = []
    for area in roadmap.get("areas") or []:
        values.append(str(area.get("status") or ""))
        for blocker in area.get("blockers") or []:
            values.append(str(blocker.get("status") or ""))
        for milestone in area.get("milestones") or []:
            values.append(str(milestone.get("status") or ""))
            for blocker in milestone.get("blockers") or []:
                values.append(str(blocker.get("status") or ""))
            for task in milestone.get("tasks") or []:
                values.append(str(task.get("status") or ""))
    return values


def _walk_json_strings(value, path=()):  # noqa: ANN001
    if isinstance(value, dict):
        for key, inner in value.items():
            yield from _walk_json_strings(inner, (*path, str(key)))
    elif isinstance(value, list):
        for index, inner in enumerate(value):
            yield from _walk_json_strings(inner, (*path, str(index)))
    elif isinstance(value, str):
        yield path, value


class TestDevDashboardRoadmapRegistryFiles(unittest.TestCase):
    def test_roadmap_json_schema_valid(self):
        schema = _read_json("docs/roadmap/setuphelfer_roadmap.schema.json")
        roadmap = _read_json("docs/roadmap/setuphelfer_roadmap.json")
        Draft202012Validator(schema).validate(roadmap)

    def test_status_values_only_from_allowed_list(self):
        roadmap = _read_json("docs/roadmap/setuphelfer_roadmap.json")
        statuses = _iter_statuses(roadmap)
        self.assertTrue(statuses)
        for status in statuses:
            self.assertIn(status, ALLOWED_STATUS_VALUES)

    def test_restore_area_present_not_green_with_reason(self):
        roadmap = _read_json("docs/roadmap/setuphelfer_roadmap.json")
        restore = next(area for area in roadmap["areas"] if area["id"] == "restore")
        self.assertIn(restore["status"], ("deferred", "blocked"))
        self.assertNotEqual(restore["status"], "green")
        decision = (restore.get("decisions") or [])[0]
        self.assertIn("bootfähiges Rettungsmedium", decision.get("decision_de") or "")
        self.assertIn("nicht-produktives Zielsystem", decision.get("decision_de") or "")

    def test_diagnostics_area_present_not_blind_green(self):
        roadmap = _read_json("docs/roadmap/setuphelfer_roadmap.json")
        diagnostics = next(area for area in roadmap["areas"] if area["id"] == "diagnostics")
        self.assertIn(diagnostics["status"], ("yellow", "partial_green"))
        self.assertNotEqual(diagnostics["status"], "green")
        self.assertIn("echte Fehlerfälle", diagnostics.get("description_de") or "")

    def test_future_test_tracks_present(self):
        roadmap = _read_json("docs/roadmap/setuphelfer_roadmap.json")
        tracks = next(area for area in roadmap["areas"] if area["id"] == "future-test-tracks")
        titles = [task.get("title_de") for milestone in tracks.get("milestones") or [] for task in milestone.get("tasks") or []]
        for expected in (
            "Windows-Laptop-Rettung",
            "Alter Linux-Laptop",
            "Raspberry Pi 5",
            "NVMe-Ziel",
            "USB-HDD-Ziel",
            "SD-Karten-Ziel",
            "Cloudserver-Edition-Test",
            "Plesk-Test",
            "Rescue-Stick-Boot-Test",
            "Restore auf nicht-produktives Zielsystem",
        ):
            self.assertIn(expected, titles)

    def test_next_prompt_registry_has_single_recommended_or_fallback(self):
        prompts = _read_json("docs/roadmap/setuphelfer_next_prompts.json")["prompts"]
        recommended = [prompt for prompt in prompts if prompt.get("status") == "recommended_next"]
        self.assertEqual(len(recommended), 1)
        for prompt in prompts:
            self.assertIn(prompt.get("status"), ALLOWED_PROMPT_STATUSES)

    def test_exported_prompt_contains_required_sections(self):
        text, error = export_next_prompt_text("DIAGNOSTICS_TEST_TRACK", repo_root=_repo)
        self.assertIsNone(error)
        assert text is not None
        self.assertIn("STRICT MODE", text)
        self.assertIn("Phase 0 Runtime-/Repo-Gate", text)
        self.assertIn("Verbotene Aktionen", text)
        self.assertIn("Kein sudo.", text)

    def test_static_dangerous_terms_only_in_allowed_prompt_keys(self):
        roadmap_text = (_repo / "docs/roadmap/setuphelfer_roadmap.json").read_text(encoding="utf-8")
        for token in ("mkfs", "dd if=", "wipefs", "parted", "mount ", "umount ", "apt upgrade", "sudo "):
            self.assertNotIn(token, roadmap_text)

        prompts = _read_json("docs/roadmap/setuphelfer_next_prompts.json")
        allowed_keys = {"safety_rules", "forbidden_actions"}
        for path, value in _walk_json_strings(prompts):
            lowered = value.lower()
            if any(token in lowered for token in ("mkfs", "dd if=", "wipefs", "parted", "mount ", "umount ", "apt upgrade", "sudo ")):
                parent_key = path[-2] if len(path) >= 2 else ""
                leaf_key = path[-1] if path else ""
                self.assertTrue(parent_key in allowed_keys or leaf_key in allowed_keys, msg=f"unexpected dangerous token at {path}")


try:
    from fastapi.testclient import TestClient
    from app import app

    _HAS_APP = True
except Exception:
    _HAS_APP = False
    TestClient = None
    app = None


@unittest.skipUnless(_HAS_APP, "FastAPI TestClient oder app nicht verfuegbar")
class TestDevDashboardRoadmapRegistryApi(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app, base_url="http://localhost")

    def test_roadmap_api_and_read_only_flags(self):
        response = self.client.get("/api/dev-dashboard/roadmap")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertIn(body.get("status"), ("success", "review_required"))
        self.assertTrue(body.get("read_only"))
        self.assertFalse(body.get("execution_allowed"))
        self.assertIn("roadmap", body)

    def test_next_prompt_api_returns_selected_prompt(self):
        response = self.client.get("/api/dev-dashboard/roadmap/next-prompt")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        prompt = body.get("prompt") or {}
        self.assertEqual(prompt.get("id"), "RESCUE_ISO_MANUAL_OPERATOR_TERMINAL_BUILD")
        self.assertTrue(body.get("read_only"))
        self.assertFalse(body.get("execution_allowed"))

    def test_export_next_prompt_returns_text(self):
        response = self.client.get("/api/dev-dashboard/roadmap/export-next-prompt/DIAGNOSTICS_TEST_TRACK")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("STRICT MODE", response.text)
        self.assertIn("Phase 0 Runtime-/Repo-Gate", response.text)

    def test_invalid_prompt_id_returns_clean_error(self):
        response = self.client.get("/api/dev-dashboard/roadmap/export-next-prompt/__missing__")
        self.assertEqual(response.status_code, 404, response.text)
        body = response.json()
        self.assertEqual(body.get("error"), "prompt_not_found")

    def test_missing_registry_files_do_not_crash(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            with patch("core.dev_dashboard_roadmap._repo_root", return_value=repo):
                with patch("core.dev_dashboard._repo_root", return_value=repo):
                    response = self.client.get("/api/dev-dashboard/roadmap")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body.get("status"), "review_required")
        self.assertTrue(body.get("read_only"))


class TestDevDashboardRoadmapRegistryBundle(unittest.TestCase):
    def test_bundle_loads_and_selects_recommended_prompt(self):
        bundle = load_roadmap_registry_bundle(repo_root=_repo)
        self.assertIn(bundle.get("status"), ("success", "review_required"))
        self.assertTrue(bundle.get("read_only"))
        self.assertFalse(bundle.get("execution_allowed"))
        self.assertEqual((bundle.get("recommended_prompt") or {}).get("id"), "RESCUE_ISO_MANUAL_OPERATOR_TERMINAL_BUILD")


if __name__ == "__main__":
    unittest.main()
