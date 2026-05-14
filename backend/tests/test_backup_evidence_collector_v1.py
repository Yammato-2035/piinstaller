"""backup_evidence_collector: robuste Erfassung bei fehlenden Rechten."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from tools import backup_evidence_collector as bec


def test_run_capture_marks_permission_denied() -> None:
    def fake_run(cmd, **kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr="Permission denied")

    with patch.object(bec.subprocess, "run", fake_run):
        r = bec._run_capture("t", ["journalctl", "-k"])
    assert r.get("permission_denied") is True


def test_run_capture_ok_stdout() -> None:
    def fake_run(cmd, **kwargs):
        return SimpleNamespace(returncode=0, stdout="ok\n", stderr="")

    with patch.object(bec.subprocess, "run", fake_run):
        r = bec._run_capture("t", ["true"])
    assert r.get("ok") is True
    assert "ok" in (r.get("stdout") or "")
