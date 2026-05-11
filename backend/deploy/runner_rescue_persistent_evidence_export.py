from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from deploy.runner_rescue_io import REPO_ROOT, ensure_rescue_workspace_dirs, guard_handoff_overwrite, resolve_handoff_path, write_json_handoff

_PLAN_REL = "docs/evidence/runtime-results/handoff/rescue_evidence_export_plan.json"
_RESULT_REL = "docs/evidence/runtime-results/handoff/rescue_evidence_export_result.json"
_HANDOFF_DIR = REPO_ROOT / "docs/evidence/runtime-results/handoff"
_MAX_BYTES = 768 * 1024


def _emit_plan(status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    return {
        "rescue_evidence_export_plan_status": status,
        "rescue_evidence_export_plan_file_path": _PLAN_REL,
        "rescue_evidence_export_plan": body,
        "rescue_evidence_export_plan_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def _emit_result(status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    return {
        "rescue_evidence_export_result_status": status,
        "rescue_evidence_export_result_file_path": _RESULT_REL,
        "rescue_evidence_export_result": body,
        "rescue_evidence_export_result_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def _export_target_allowed(raw: str) -> tuple[bool, str]:
    s = (raw or "").strip().replace("\\", "/")
    if not s:
        return False, "EMPTY"
    if s in ("/", "/boot", "/efi", "/home", "/root"):
        return False, "BLOCKED_SYSTEM_ROOT"
    low = s.lower()
    if low.startswith("/boot") or low.startswith("/efi") or low == "/home" or low.startswith("/home/") or low.startswith("/root/"):
        return False, "BLOCKED_SYSTEM_PREFIX"
    if low.startswith("build/rescue/evidence/export/") or low == "build/rescue/evidence/export":
        return True, ""
    if low.startswith("/media") or low.startswith("/run/media"):
        return True, ""
    return False, "TARGET_NOT_IN_ALLOWLIST"


def build_rescue_evidence_export_plan(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_PLAN_REL, "RESCUE_EVPLAN")
    if oerr or out_path is None:
        return _emit_plan("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_EVPLAN_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_EVPLAN")
    if gerr:
        return _emit_plan("blocked", {}, wrote=False, warnings=[], errors=[gerr])

    ensure_rescue_workspace_dirs()
    body: dict[str, Any] = {
        "rescue_evidence_export_plan_schema_version": 1,
        "strict_mode": "rescue_evidence_export_controlled",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "allowed_target_prefixes": ["build/rescue/evidence/export/", "/media/", "/run/media/"],
        "forbidden_targets": ["/", "/boot", "/efi", "/home", "/root"],
        "formats": ["tar", "zip"],
        "no_auto_target_selection": True,
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BYTES)
    if werr:
        return _emit_plan("blocked", body, wrote=False, warnings=[], errors=[werr])
    return _emit_plan("ok", body, wrote=True, warnings=[], errors=[])


def execute_rescue_evidence_export(
    *,
    explicit_overwrite: bool = False,
    explicit_execute_evidence_export: bool = False,
    export_target: str | None = None,
) -> dict[str, Any]:
    if not explicit_execute_evidence_export:
        return _emit_result(
            "blocked",
            {"reason": "EXECUTE_REQUIRES_EXPLICIT_EVIDENCE_EXPORT"},
            wrote=False,
            warnings=[],
            errors=["EXECUTE_REQUIRES_EXPLICIT_EVIDENCE_EXPORT"],
        )

    ok, reason = _export_target_allowed(str(export_target or ""))
    if not ok:
        return _emit_result(
            "blocked",
            {"reason": reason, "export_target": export_target},
            wrote=False,
            warnings=[],
            errors=[f"RESCUE_EVIDENCE_TARGET_{reason}"],
        )

    out_path, oerr = resolve_handoff_path(_RESULT_REL, "RESCUE_EVRES")
    if oerr or out_path is None:
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_EVRES_INVALID"])
    g0 = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_EVRES")
    if g0:
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=[g0])

    rel = str(export_target).strip().replace("\\", "/")
    if rel.startswith("build/rescue/"):
        dest = (REPO_ROOT / rel).resolve()
        try:
            dest.relative_to(REPO_ROOT.resolve(strict=False))
        except ValueError:
            return _emit_result("blocked", {}, wrote=False, warnings=[], errors=["RESCUE_EVIDENCE_TARGET_OUTSIDE_REPO"])
    else:
        dest = Path(rel).resolve()
        roots = (Path("/media").resolve(strict=False), Path("/run/media").resolve(strict=False))
        ok_root = False
        for r in roots:
            try:
                dest.relative_to(r)
                ok_root = True
                break
            except ValueError:
                continue
        if not ok_root:
            return _emit_result("blocked", {}, wrote=False, warnings=[], errors=["RESCUE_EVIDENCE_TARGET_NOT_UNDER_MEDIA"])

    try:
        dest.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=[f"RESCUE_EVIDENCE_MKDIR:{e!s}"])
    copied: list[str] = []
    for p in sorted(_HANDOFF_DIR.glob("rescue_*.json")):
        if p.is_file():
            target = dest / p.name
            shutil.copy2(p, target)
            try:
                rel = str(target.resolve().relative_to(REPO_ROOT.resolve())).replace("\\", "/")
            except ValueError:
                rel = str(target)
            copied.append(rel)

    raw: dict[str, Any] = {
        "rescue_evidence_export_result_schema_version": 1,
        "strict_mode": "rescue_evidence_export_controlled",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "export_target": str(export_target).replace("\\", "/"),
        "files_copied": copied[:200],
        "archive_format": "copy_only",
    }
    werr = write_json_handoff(out_path, raw, max_bytes=_MAX_BYTES)
    if werr:
        return _emit_result("blocked", raw, wrote=False, warnings=[], errors=[werr])
    return build_rescue_evidence_export_result(explicit_overwrite=True)


def build_rescue_evidence_export_result(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_RESULT_REL, "RESCUE_EVRES")
    if oerr or out_path is None:
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_EVRES_INVALID"])
    if not out_path.is_file():
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=["RESCUE_EVRES_MISSING"])
    g1 = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_EVRES")
    if g1:
        return _emit_result("blocked", {}, wrote=False, warnings=[], errors=[g1])

    data = json.loads(out_path.read_text(encoding="utf-8"))
    n = len(data.get("files_copied") or [])
    merged = dict(data)
    merged["evaluation"] = {
        "rescue_evidence_export_eval_status": "ok" if n else "review_required",
        "files_exported": n,
    }
    werr = write_json_handoff(out_path, merged, max_bytes=_MAX_BYTES)
    if werr:
        return _emit_result("blocked", merged, wrote=False, warnings=[], errors=[werr])
    st = "ok" if n else "review_required"
    return _emit_result(st, merged, wrote=True, warnings=[], errors=[])
