"""Tests for rescue UI static server + API proxy (RS-P3A)."""

from __future__ import annotations

import json
import threading
import urllib.request
from http.server import HTTPServer
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SERVE = REPO / "scripts/rescue-live/rescue_ui_serve.py"


import http.server


class _FakeBackendHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if self.path.startswith("/api/rescue/storage/discovery"):
            body = json.dumps(
                {"source_candidates": [{"path": "/dev/nvme0n1"}], "target_candidates": []}
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args, **kwargs):
        return


def _import_handler():
    import importlib.util

    spec = importlib.util.spec_from_file_location("rescue_ui_serve", SERVE)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod.RescueUIHandler


def test_rescue_ui_proxy_forwards_api(tmp_path: Path):
    ui_root = tmp_path / "ui"
    ui_root.mkdir()
    (ui_root / "rescue.html").write_text("<html>ok</html>", encoding="utf-8")

    import http.server

    backend = HTTPServer(("127.0.0.1", 0), _FakeBackendHandler)
    backend_port = backend.server_address[1]
    t = threading.Thread(target=backend.serve_forever, daemon=True)
    t.start()

    Handler = _import_handler()
    from functools import partial

    handler = partial(Handler, spa_root=ui_root, upstream=f"http://127.0.0.1:{backend_port}")
    ui = HTTPServer(("127.0.0.1", 0), handler)
    ui_port = ui.server_address[1]
    t2 = threading.Thread(target=ui.serve_forever, daemon=True)
    t2.start()

    with urllib.request.urlopen(f"http://127.0.0.1:{ui_port}/api/rescue/storage/discovery", timeout=5) as resp:
        data = json.loads(resp.read().decode())
    assert data["source_candidates"][0]["path"] == "/dev/nvme0n1"

    with urllib.request.urlopen(f"http://127.0.0.1:{ui_port}/rescue.html", timeout=5) as resp:
        assert b"ok" in resp.read()

    backend.shutdown()
    ui.shutdown()


def test_discover_rescue_storage_mocked_lsblk(monkeypatch):
    from core.rescue_storage_discovery import discover_rescue_storage

    tree = [
        {
            "name": "nvme0n1",
            "path": "/dev/nvme0n1",
            "type": "disk",
            "size": 1000000000000,
            "fstype": "",
            "label": "",
            "mountpoints": [None],
            "tran": "nvme",
            "rm": False,
            "children": [
                {
                    "name": "nvme0n1p3",
                    "path": "/dev/nvme0n1p3",
                    "type": "part",
                    "size": 500000000000,
                    "fstype": "ntfs",
                    "label": "Windows",
                    "mountpoints": [None],
                    "tran": "nvme",
                    "rm": False,
                }
            ],
        },
        {
            "name": "sdb",
            "path": "/dev/sdb",
            "type": "disk",
            "size": 2000000000000,
            "fstype": "",
            "label": "BACKUP",
            "mountpoints": [None],
            "tran": "usb",
            "rm": True,
        },
    ]

    monkeypatch.setattr("core.rescue_storage_discovery._lsblk_tree", lambda: tree)
    monkeypatch.setattr("core.rescue_storage_discovery._blkid_type_map", lambda: {})

    out = discover_rescue_storage()
    source_paths = {d["path"] for d in out["source_candidates"]}
    target_paths = {d["path"] for d in out["target_candidates"]}
    assert "/dev/nvme0n1" in source_paths
    assert "/dev/sdb" in target_paths
    assert out["target_candidates"][0]["role"] == "backup_target"
