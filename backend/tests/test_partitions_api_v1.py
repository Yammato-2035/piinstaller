"""
Partitionshelfer API v1 – Phase-1 read-only contract tests.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import partitions as partitions_mod
from api.routes.partitions import partition_router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(partition_router, prefix="/api/partitions")
    return TestClient(app)


def test_scan_route_registered_not_404(client):
    r = client.get("/api/partitions/scan")
    assert r.status_code != 404
    assert r.status_code == 200
    body = r.json()
    assert "disks" in body
    assert "scanned_at" in body
    assert isinstance(body["disks"], list)


def test_openapi_lists_partition_paths(client):
    app = client.app
    paths = app.openapi().get("paths", {})
    assert "/api/partitions/scan" in paths
    assert "get" in paths["/api/partitions/scan"]
    assert "/api/partitions/safety-check" in paths
    assert "/api/partitions/queue" in paths


def test_safety_check_is_read_only(client):
    r = client.get(
        "/api/partitions/safety-check",
        params={"partition": "nonexistent-partition-xyz", "action": "delete"},
    )
    assert r.status_code == 404
    assert partitions_mod._queue == []


def test_queue_apply_does_not_execute_writes(client):
    partitions_mod._queue.clear()
    r = client.post("/api/partitions/queue/apply", json={"confirmed": True})
    assert r.status_code == 200
    data = r.json()
    assert data.get("erfolg") == 0
    assert "Phase 2" in (data.get("message") or "")


def test_partitions_route_module_has_no_disk_write_tools():
    src = Path(partitions_mod.__file__).read_text(encoding="utf-8")
    assert "mkfs" not in src
    assert "parted" not in src
    assert "subprocess" not in src
    assert "sfdisk" not in src


def test_apply_queue_never_reports_successful_writes(client):
    partitions_mod._queue.clear()
    r = client.post("/api/partitions/queue/apply", json={"confirmed": True})
    assert r.json().get("erfolg") == 0


def test_tkinter_fallback_still_present():
    root = Path(__file__).resolve().parents[2] / "apps" / "partitionshelfer"
    assert (root / "start.py").is_file()
    assert (root / "ui" / "main_window.py").is_file()
