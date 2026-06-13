"""
Rescue evidence bundle — aggregate boot, matrix, MSI, telemetry summaries (Phase R.3).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.rescue_boot_logger import write_boot_evidence_bundle
from core.rescue_msi_diagnostics import write_msi_diagnostics_evidence
from core.rescue_persistence import Runner, write_rescue_json_evidence, write_rescue_text_evidence
from core.rescue_telemetry_spool import build_telemetry_spool_summary
from core.rescue_test_matrix import write_rescue_test_matrix

RESCUE_EVIDENCE_BUNDLE_VERSION = 3


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_rescue_evidence_bundle(*, runner: Runner = None, include_msi: bool = True) -> dict[str, Any]:
    """Collect all R.3 evidence slices into one summary document."""
    boot_result = write_boot_evidence_bundle(runner=runner)
    matrix_result = write_rescue_test_matrix(runner=runner)
    telemetry_summary = build_telemetry_spool_summary(runner=runner)
    msi_result: dict[str, Any] | None = None
    if include_msi:
        msi_result = write_msi_diagnostics_evidence(runner=runner)

    matrix_doc = matrix_result.get("document") if isinstance(matrix_result.get("document"), dict) else {}
    blockers = [
        e for e in (matrix_doc.get("entries") or []) if isinstance(e, dict) and e.get("status") in ("red", "blocked")
    ]
    warnings = [
        e for e in (matrix_doc.get("entries") or []) if isinstance(e, dict) and e.get("status") == "yellow"
    ]

    bundle = {
        "schema_version": 1,
        "bundle_version": RESCUE_EVIDENCE_BUNDLE_VERSION,
        "generated_at": _utc_now(),
        "boot": boot_result,
        "matrix": matrix_result,
        "telemetry_spool": telemetry_summary,
        "msi_diagnostics": msi_result,
        "open_blockers": blockers[:20],
        "warnings": warnings[:20],
        "policy": {
            "internal_disk_writes": False,
            "backup_execute": False,
            "restore_execute": False,
            "partition_writes": False,
        },
    }
    bundle["next_actions"] = build_rescue_next_actions(bundle)
    return bundle


def build_rescue_next_actions(bundle: dict[str, Any] | None = None) -> list[str]:
    """Derive prioritized next actions from bundle/matrix."""
    actions: list[str] = []
    if bundle and isinstance(bundle.get("matrix"), dict):
        doc = bundle["matrix"].get("document")
        if isinstance(doc, dict):
            for e in doc.get("entries") or []:
                if not isinstance(e, dict):
                    continue
                if e.get("id") == "R3-NEXT-001" and e.get("next_action"):
                    actions.append(str(e["next_action"]))
                    break
    if bundle:
        for b in bundle.get("open_blockers") or []:
            if isinstance(b, dict) and b.get("next_action"):
                actions.append(str(b["next_action"]))
    if not actions:
        actions.append("Stick-Boot erneut prüfen und /setuphelfer-evidence/ auf dem Medium verifizieren")
    seen: set[str] = set()
    unique: list[str] = []
    for a in actions:
        if a not in seen:
            seen.add(a)
            unique.append(a)
    return unique[:8]


def write_rescue_evidence_bundle(*, runner: Runner = None, include_msi: bool = True) -> dict[str, Any]:
    bundle = build_rescue_evidence_bundle(runner=runner, include_msi=include_msi)
    json_result = write_rescue_json_evidence("summaries", "rescue_evidence_latest.json", bundle, runner=runner)
    lines = [
        "# Setuphelfer Rescue Evidence Bundle R.3",
        f"generated_at: {bundle.get('generated_at')}",
        "",
        "## Status",
        f"blockers: {len(bundle.get('open_blockers') or [])}",
        f"warnings: {len(bundle.get('warnings') or [])}",
        "",
        "## Nächste Aktionen",
    ]
    for i, act in enumerate(bundle.get("next_actions") or [], 1):
        lines.append(f"{i}. {act}")
    text_result = write_rescue_text_evidence("summaries", "rescue_evidence_latest.md", "\n".join(lines), runner=runner)
    return {
        "status": "ok",
        "bundle": bundle,
        "json": json_result,
        "markdown": text_result,
        "evidence_root": json_result.get("path", "").replace("/summaries/rescue_evidence_latest.json", ""),
    }


def build_rescue_evidence_bundle_diagnostics() -> dict[str, Any]:
    return {
        "bundle_version": RESCUE_EVIDENCE_BUNDLE_VERSION,
        "module": "core.rescue_evidence_bundle",
        "public_functions": [
            "build_rescue_evidence_bundle",
            "write_rescue_evidence_bundle",
            "build_rescue_next_actions",
            "build_rescue_evidence_bundle_diagnostics",
        ],
    }
