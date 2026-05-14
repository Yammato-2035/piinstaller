"""Regression: backup_runner finalization must not triple-scan archives (BR-012)."""

from __future__ import annotations

import io
import tarfile
from pathlib import Path

import pytest

from tools import backup_runner as br


def test_throttled_finalize_emits_on_phase_change() -> None:
    calls: list[tuple[str, int]] = []

    def cb(phase: str, n: int) -> None:
        calls.append((phase, n))

    st: dict = {"t": 0.0, "phase": ""}
    br._throttled_finalize_progress(cb, phase="a", processed=1, state=st)
    br._throttled_finalize_progress(cb, phase="a", processed=2, state=st)
    br._throttled_finalize_progress(cb, phase="b", processed=3, state=st)
    assert [c[0] for c in calls] == ["a", "b"]


def test_sha256_archive_payload_streams_and_reports_progress(tmp_path: Path) -> None:
    """Large-enough payload triggers progress without loading whole file into RAM at once."""
    arc = tmp_path / "t.tar.gz"
    chunk = b"x" * (2 * 1024 * 1024)
    bio = io.BytesIO()
    with tarfile.open(fileobj=bio, mode="w:gz") as tf:
        ti = tarfile.TarInfo(name="big.bin")
        ti.size = len(chunk)
        tf.addfile(ti, io.BytesIO(chunk))
        ti2 = tarfile.TarInfo(name="small.txt")
        ti2.size = 3
        tf.addfile(ti2, io.BytesIO(b"abc"))
    arc.write_bytes(bio.getvalue())

    hits: list[tuple[str, int]] = []

    def prog(phase: str, n: int) -> None:
        hits.append((phase, n))

    h = br._sha256_archive_payload(arc, progress=prog, progress_state={"t": 0.0, "phase": ""})
    assert len(h) == 64
    assert any(p[0] == "finalizing_hash" for p in hits)
    assert hits[-1][0] == "finalizing_hash"


def test_rewrite_manifest_preserves_payload_hash(tmp_path: Path) -> None:
    arc = tmp_path / "p.tar.gz.partial"
    payload = b"payload-bytes"
    bio = io.BytesIO()
    with tarfile.open(fileobj=bio, mode="w:gz") as tf:
        ti = tarfile.TarInfo(name="data.bin")
        ti.size = len(payload)
        tf.addfile(ti, io.BytesIO(payload))
    arc.write_bytes(bio.getvalue())

    h_before = br._sha256_archive_payload(arc)
    manifest = {
        "job_id": "test",
        "backup_type": "full",
        "source": "/",
        "backup_dir": str(tmp_path),
        "created_at": "2026-01-01T00:00:00+00:00",
        "completed_at": "2026-01-01T00:00:01+00:00",
        "archive_size": str(arc.stat().st_size),
        "hash": f"sha256:{h_before}",
    }
    ok, err = br._rewrite_manifest_in_archive(arc, manifest)
    assert ok, err
    h_after = br._sha256_archive_payload(arc)
    assert h_before == h_after
