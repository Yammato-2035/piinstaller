from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from deploy.runner_rescue_io import guard_handoff_overwrite, load_json_handoff, resolve_handoff_path, write_json_handoff

_OUT_REL = "docs/evidence/runtime-results/handoff/rescue_hardware_recovery_test_chain.json"
_MAX_BYTES = 768 * 1024


def _emit(status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    return {
        "rescue_hardware_recovery_test_chain_status": status,
        "rescue_hardware_recovery_test_chain_file_path": _OUT_REL,
        "rescue_hardware_recovery_test_chain": body,
        "rescue_hardware_recovery_test_chain_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def _nav(d: dict[str, Any], path: str) -> Any:
    o: Any = d
    for k in path.split("."):
        if not isinstance(o, dict):
            return None
        o = o.get(k)
    return o


def _read_step(rel: str, rule: tuple[str, Any] | None) -> dict[str, Any]:
    data, err = load_json_handoff(rel, "RESCUE_HWCHAIN")
    if err:
        st = "missing" if "MISSING" in err else "error"
        return {"handoff": rel, "present": False, "status": st, "detail": str(err)}
    if not isinstance(data, dict):
        return {"handoff": rel, "present": False, "status": "error", "detail": "INVALID_JSON_SHAPE"}
    if rule is None:
        return {"handoff": rel, "present": True, "status": "ok", "detail": ""}
    keypath, want = rule
    got = _nav(data, keypath)
    ok = got == want
    return {
        "handoff": rel,
        "present": True,
        "status": "ok" if ok else "review_required",
        "detail": "" if ok else f"expected {want!r} at {keypath}, got {got!r}",
    }


def _final_gate_step(rel: str) -> dict[str, Any]:
    data, err = load_json_handoff(rel, "RESCUE_HWCHAIN")
    if err:
        st = "missing" if "MISSING" in err else "error"
        return {"handoff": rel, "present": False, "status": st, "detail": str(err)}
    if not isinstance(data, dict):
        return {"handoff": rel, "present": False, "status": "error", "detail": "INVALID_JSON_SHAPE"}
    inner = data.get("rescue_final_recovery_readiness_gate") if isinstance(data.get("rescue_final_recovery_readiness_gate"), dict) else data
    gs = str(inner.get("gate_status") or "") if isinstance(inner, dict) else ""
    ok = gs == "ready"
    return {
        "handoff": rel,
        "present": True,
        "status": "ok" if ok else "review_required",
        "detail": "" if ok else f"gate_status={gs!r}",
    }


def build_rescue_hardware_recovery_test_chain(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_OUT_REL, "RESCUE_HWCHAIN")
    if oerr or out_path is None:
        return _emit("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_HWCHAIN_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_HWCHAIN")
    if gerr:
        return _emit("blocked", {}, wrote=False, warnings=[], errors=[gerr])

    steps: list[dict[str, Any]] = [
        {"id": "iso_boot", "label": "ISO boot / readiness", **_read_step("docs/evidence/runtime-results/handoff/rescue_iso_readiness_gate.json", ("gate_status", "ready"))},
        {
            "id": "storage_discovery",
            "label": "Storage discovery",
            **_read_step(
                "docs/evidence/runtime-results/handoff/rescue_storage_discovery_result.json",
                ("evaluation.rescue_storage_discovery_eval_status", "ok"),
            ),
        },
        {
            "id": "readonly_mounts",
            "label": "Readonly mounts",
            **_read_step(
                "docs/evidence/runtime-results/handoff/readonly_mount_result.json",
                ("evaluation.readonly_mount_eval_status", "ok"),
            ),
        },
        {"id": "efi_analysis", "label": "EFI analysis", **_read_step("docs/evidence/runtime-results/handoff/rescue_efi_boot_analysis.json", None)},
        {
            "id": "backup_discovery",
            "label": "Backup discovery",
            **_read_step(
                "docs/evidence/runtime-results/handoff/rescue_backup_verify_result.json",
                ("discovery.manifest_present", True),
            ),
        },
        {
            "id": "verify",
            "label": "Backup verify",
            **_read_step(
                "docs/evidence/runtime-results/handoff/rescue_backup_verify_result.json",
                ("evaluation.rescue_backup_verify_eval_status", "ok"),
            ),
        },
        {
            "id": "restore_preview",
            "label": "Restore preview",
            **_read_step(
                "docs/evidence/runtime-results/handoff/rescue_restore_preview_result.json",
                ("evaluation.rescue_restore_preview_eval_status", "ok"),
            ),
        },
        {
            "id": "evidence_export",
            "label": "Evidence export",
            **_read_step(
                "docs/evidence/runtime-results/handoff/rescue_evidence_export_result.json",
                ("evaluation.rescue_evidence_export_eval_status", "ok"),
            ),
        },
        {
            "id": "final_readonly_recovery_assessment",
            "label": "Final readonly recovery assessment",
            **_final_gate_step("docs/evidence/runtime-results/handoff/rescue_final_recovery_readiness_gate.json"),
        },
    ]

    warnings: list[str] = []
    bad = [s for s in steps if s.get("status") != "ok"]
    if bad:
        warnings.append("RESCUE_HWCHAIN_INCOMPLETE")

    st = "ok" if not bad else "review_required"

    body: dict[str, Any] = {
        "rescue_hardware_recovery_test_chain_schema_version": 1,
        "strict_mode": "rescue_hardware_recovery_readonly_chain",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "steps": steps,
        "chain_summary_status": st,
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BYTES)
    if werr:
        return _emit("blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit(st, body, wrote=True, warnings=warnings, errors=[])
