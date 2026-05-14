from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_scripts = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_scripts) not in sys.path:
    sys.path.insert(0, str(_scripts))

import runtime_deploy_gate_eval as rde  # noqa: E402


def test_evaluate_version_ok(tmp_path: Path) -> None:
    ws = tmp_path / "version.json"
    ws.write_text(
        json.dumps(
            {
                "project_version": "1.7.1",
                "version_source_of_truth": True,
            }
        ),
        encoding="utf-8",
    )
    api = {
        "status": "success",
        "project_version": "1.7.1",
        "install_profile": "opt",
        "app_edition": "release",
        "backend_runtime_path": "/opt/setuphelfer/backend",
    }
    assert rde.evaluate_version_payload(api, ws) == 0


def test_evaluate_version_mismatch(tmp_path: Path) -> None:
    ws = tmp_path / "version.json"
    ws.write_text(json.dumps({"project_version": "9.0.0", "version_source_of_truth": True}), encoding="utf-8")
    api = {"status": "success", "project_version": "1.0.0", "install_profile": "repo", "app_edition": "repo"}
    assert rde.evaluate_version_payload(api, ws) == 12


def test_evaluate_runtime_path_invalid() -> None:
    ws = Path(__file__).resolve().parent.parent.parent / "config" / "version.json"
    if not ws.is_file():
        pytest.skip("config/version.json fehlt")
    api = {
        "status": "success",
        "project_version": json.loads(ws.read_text(encoding="utf-8")).get("project_version", "0.0.0"),
        "install_profile": "opt",
        "app_edition": "release",
        "backend_runtime_path": "/wrong/backend",
    }
    assert rde.evaluate_version_payload(api, ws) == 13


def test_deploy_drift_manifest_mismatch() -> None:
    body = {"deploy_drift": {"status": "green", "manifest_match": False, "suggested_actions": ["none"]}}
    assert rde.evaluate_deploy_drift(body, allow_gray=False) == 16


def test_deploy_drift_yellow_deploy_files() -> None:
    body = {
        "deploy_drift": {
            "status": "yellow",
            "manifest_match": None,
            "suggested_actions": ["deploy_backend_files", "restart_backend_manual"],
        }
    }
    assert rde.evaluate_deploy_drift(body, allow_gray=False) == 14


def test_deploy_drift_yellow_restart_only() -> None:
    body = {
        "deploy_drift": {
            "status": "yellow",
            "manifest_match": True,
            "suggested_actions": ["restart_backend_manual", "rebuild_frontend"],
        }
    }
    assert rde.evaluate_deploy_drift(body, allow_gray=False) == 15


def test_deploy_drift_gray_blocked_without_env() -> None:
    body = {"deploy_drift": {"status": "gray", "suggested_actions": ["none"]}}
    assert rde.evaluate_deploy_drift(body, allow_gray=False) == 20


def test_deploy_drift_gray_allowed() -> None:
    body = {"deploy_drift": {"status": "gray", "suggested_actions": ["none"]}}
    assert rde.evaluate_deploy_drift(body, allow_gray=True) == 0
