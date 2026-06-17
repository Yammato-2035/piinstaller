"""
Rescue stick local evidence store — paths and writers (no internal disk writes by default).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.rescue_evidence_bundle import build_rescue_evidence_bundle, write_rescue_evidence_bundle
from core.rescue_persistence import Runner, build_rescue_evidence_root, ensure_rescue_evidence_tree

STORE_VERSION = 1

RUNTIME_EVIDENCE_DIR = "/run/setuphelfer/evidence"
PERSISTENT_EVIDENCE_DIR = "/var/lib/setuphelfer-rescue/evidence"
STICK_EVIDENCE_LABEL = "SETUPHELFER-EVIDENCE"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def evidence_store_paths(*, runner: Runner = None) -> dict[str, str]:
    meta = ensure_rescue_evidence_tree(runner=runner)
    root = str(meta.get("evidence_root") or RUNTIME_EVIDENCE_DIR)
    return {
        "runtime": RUNTIME_EVIDENCE_DIR,
        "persistent": PERSISTENT_EVIDENCE_DIR,
        "active_root": root,
        "stick_media_hint": f"/media/setuphelfer/{STICK_EVIDENCE_LABEL}",
    }


def evidence_store_status(*, runner: Runner = None) -> dict[str, Any]:
    paths = evidence_store_paths(runner=runner)
    from core.rescue_setup_logs_persistence import resolve_rescue_evidence_root

    persist = resolve_rescue_evidence_root(runner=runner)
    stick = build_rescue_evidence_root(runner=runner)
    return {
        "schema_version": 1,
        "store_version": STORE_VERSION,
        "generated_at": _utc_now(),
        "paths": paths,
        "persistence": persist,
        "stick_persistence": stick,
        "writable": bool(persist.get("persistent")),
        "fallback": persist.get("non_persistent"),
        "non_persistent": bool(persist.get("non_persistent")),
        "warning": persist.get("warning"),
        "policy": {
            "no_internal_disk_writes": True,
            "no_backup_hdd_evidence_except_manifest": True,
            "network_upload_attempted": False,
        },
    }


def write_telemetry_event_safe(event: dict[str, Any], *, runner: Runner = None) -> dict[str, Any]:
    from core.rescue_local_telemetry_queue import enqueue_local_telemetry_event

    return enqueue_local_telemetry_event(event, runner=runner)


def write_session_evidence_bundle(*, runner: Runner = None, include_msi: bool = True) -> dict[str, Any]:
    return write_rescue_evidence_bundle(runner=runner, include_msi=include_msi)


def build_session_evidence_preview(*, runner: Runner = None) -> dict[str, Any]:
    return build_rescue_evidence_bundle(runner=runner, include_msi=True)
