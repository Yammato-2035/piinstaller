"""backup_progress.merge_progress_optional"""

from __future__ import annotations

import time

from core.backup_progress import merge_progress_optional, quick_target_preflight


def test_merge_preserves_existing_finalize_keys() -> None:
    st = {"last_bytes": 0, "last_t": time.monotonic()}
    base = {"finalize_phase": "finalizing_manifest", "finalize_bytes_processed": 12}
    t0 = time.monotonic()
    out = merge_progress_optional(
        base,
        phase="archiving",
        bytes_current=100,
        bytes_total_estimate=None,
        start_monotonic=t0,
        compression_method="pigz",
        current_operation="tar",
        target_mount="/media/x",
        target_free_bytes=999,
        warning_codes=[],
        health_flags={},
        throughput_state=st,
    )
    assert out["phase"] == "archiving"
    assert out["bytes_total_estimate"] is None
    assert out["compression_method"] == "pigz"


def test_quick_target_preflight_tmp() -> None:
    r = quick_target_preflight("/tmp")
    assert r.get("target_free_bytes") is not None
