from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from deploy.runner_rescue_io import REPO_ROOT, guard_handoff_overwrite, resolve_handoff_path, write_json_handoff

_OUT_REL = "docs/evidence/runtime-results/handoff/rescue_recovery_evidence_timeline.json"
_MAX_BYTES = 1_500_000

_TIMELINE: list[tuple[str, str]] = [
    ("iso_boot", "docs/evidence/runtime-results/handoff/rescue_iso_readiness_gate.json"),
    ("discovery", "docs/evidence/runtime-results/handoff/rescue_storage_discovery_result.json"),
    ("mounts", "docs/evidence/runtime-results/handoff/readonly_mount_result.json"),
    ("efi", "docs/evidence/runtime-results/handoff/rescue_efi_boot_analysis.json"),
    ("backup_discovery", "docs/evidence/runtime-results/handoff/rescue_backup_verify_result.json"),
    ("verify", "docs/evidence/runtime-results/handoff/rescue_backup_verify_result.json"),
    ("restore_preview", "docs/evidence/runtime-results/handoff/rescue_restore_preview_result.json"),
    ("export", "docs/evidence/runtime-results/handoff/rescue_evidence_export_result.json"),
    ("readiness_gate", "docs/evidence/runtime-results/handoff/rescue_final_recovery_readiness_gate.json"),
]


def _emit(status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    return {
        "rescue_recovery_evidence_timeline_status": status,
        "rescue_recovery_evidence_timeline_file_path": _OUT_REL,
        "rescue_recovery_evidence_timeline": body,
        "rescue_recovery_evidence_timeline_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def build_rescue_recovery_evidence_timeline(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_OUT_REL, "RESCUE_RET")
    if oerr or out_path is None:
        return _emit("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_RET_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_RET")
    if gerr:
        return _emit("blocked", {}, wrote=False, warnings=[], errors=[gerr])

    entries: list[dict[str, Any]] = []
    warnings: list[str] = []

    for step_id, rel in _TIMELINE:
        p = REPO_ROOT / rel
        if not p.is_file():
            entries.append(
                {
                    "step_id": step_id,
                    "handoff_relative": rel,
                    "present": False,
                    "sha256": None,
                    "byte_length": 0,
                }
            )
            warnings.append(f"RESCUE_RET_MISSING:{step_id}")
            continue
        raw = p.read_bytes()
        h = hashlib.sha256(raw).hexdigest()
        entries.append(
            {
                "step_id": step_id,
                "handoff_relative": rel,
                "present": True,
                "sha256": h,
                "byte_length": len(raw),
            }
        )

    st = "ok" if not warnings else "review_required"

    body: dict[str, Any] = {
        "rescue_recovery_evidence_timeline_schema_version": 1,
        "strict_mode": "rescue_recovery_evidence_readonly",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "entries": entries,
        "sha256_over_raw_bytes": True,
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BYTES)
    if werr:
        return _emit("blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit(st, body, wrote=True, warnings=warnings, errors=[])
