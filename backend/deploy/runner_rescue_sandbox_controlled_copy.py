from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from deploy.runner_rescue_io import (
    BUILD_RESCUE_ROOT,
    REPO_ROOT,
    atomic_write_text,
    guard_handoff_overwrite,
    load_json_handoff,
    resolve_handoff_path,
    resolve_under_build_rescue,
    write_json_handoff,
)

_MAX_MANIFEST = 900_000
_MAX_HANDOFF = 512 * 1024
_MAX_COPY_BYTES = 5 * 1024 * 1024
_MAX_ENTRIES = 220

_MANIFEST = "build/rescue/sandbox_root_manifest.json"
_CFG_PLAN = "build/rescue/sandbox_config_copy_plan.json"
_RT_PLAN = "build/rescue/sandbox_runtime_copy_plan.json"
_SB_FIN = "docs/evidence/runtime-results/handoff/rescue_build_sandbox_final_gate.json"
_SB_SAFE = "docs/evidence/runtime-results/handoff/rescue_build_sandbox_safety.json"

_PRECHECK = "docs/evidence/runtime-results/handoff/rescue_sandbox_copy_execution_precheck.json"
_CFG_RESULT = "build/rescue/sandbox/manifests/config_copy_result.json"
_RT_RESULT = "build/rescue/sandbox/manifests/runtime_copy_result.json"
_VERIFY = "docs/evidence/runtime-results/handoff/rescue_sandbox_copy_verify_result.json"
_SEAL = "build/rescue/sandbox/manifests/sandbox_copy.seal.json"
_COPY_FIN = "docs/evidence/runtime-results/handoff/rescue_sandbox_copy_final_gate.json"

_BRAND = "docs/evidence/runtime-results/handoff/setuphelfer_branding_guard_check.json"
_ZERO = "docs/evidence/runtime-results/handoff/runtime_identifier_zero_state_verification.json"

_PREFIX_CFG = "build/rescue/sandbox/config-copy/"
_PREFIX_RT = "build/rescue/sandbox/runtime-copy/"

_TEXT_SUFFIXES = (
    ".json",
    ".md",
    ".txt",
    ".cfg",
    ".template",
    ".list",
    ".chroot",
    ".yaml",
    ".yml",
)

_BLOCKED_PARTS = frozenset({"node_modules", ".git", "dist-cache"})
_BLOCKED_SUF = (".iso", ".img", ".qcow2", ".qcow", ".vdi", ".vmdk")
_LEGACY_PI = re.compile(r"(?<![A-Za-z0-9_])pi[-_]installer(?![A-Za-z0-9_])")


def _entry_optional(e: dict[str, Any]) -> bool:
    if e.get("copy_optional") is True or e.get("optional") is True:
        return True
    return str(e.get("copy_mode") or "") == "optional_copy"


def _emit(prefix: str, file_rel: str, status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    sk = f"{prefix}_status"
    return {
        sk: status,
        f"{prefix}_file_path": file_rel,
        prefix: body,
        f"{prefix}_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def _build_path(rel: str) -> tuple[Path | None, str | None]:
    raw = rel if rel.startswith("build/rescue/") else f"build/rescue/{rel.lstrip('/')}"
    return resolve_under_build_rescue(raw, "RESCUE_SCCOPY")


def _repo_path(rel: str) -> Path | None:
    r = rel.replace("\\", "/").strip()
    if not r or ".." in r or r.startswith("/"):
        return None
    return REPO_ROOT / r


def _under_sandbox_resolved(p: Path) -> bool:
    try:
        p.resolve(strict=False).relative_to((BUILD_RESCUE_ROOT / "sandbox").resolve(strict=False))
    except (OSError, ValueError):
        return False
    return True


def _is_textish_suffix(name: str) -> bool:
    low = name.lower()
    return any(low.endswith(s) for s in _TEXT_SUFFIXES)


def _path_blocked(rel: str) -> str | None:
    low = rel.lower()
    for suf in _BLOCKED_SUF:
        if low.endswith(suf):
            return suf
    for part in Path(rel).parts:
        if part in _BLOCKED_PARTS or part.lower() in ("node_modules", "dist-cache"):
            return part
    return None


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(fp: Path) -> str | None:
    try:
        data = fp.read_bytes()
    except OSError:
        return None
    return _sha256_bytes(data)


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)


def _looks_binary(data: bytes) -> bool:
    sample = data[:65536]
    return b"\x00" in sample


def _load_plan(rel: str) -> tuple[list[dict[str, Any]] | None, str | None]:
    p, err = _build_path(rel)
    if err or p is None or not p.is_file():
        return None, err or "MISSING"
    try:
        o = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, "JSON"
    entries = o.get("plan_entries") if isinstance(o.get("plan_entries"), list) else []
    out: list[dict[str, Any]] = []
    for e in entries:
        if isinstance(e, dict):
            out.append(e)
    return out, None


def build_rescue_sandbox_copy_execution_precheck(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_PRECHECK, "RESCUE_SCCOPY_PC")
    if oerr or out_path is None:
        return _emit("rescue_sandbox_copy_execution_precheck", _PRECHECK, "blocked", {}, wrote=False, warnings=[], errors=[oerr or "INVALID"])
    g0 = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_SCCOPY_PC")
    if g0:
        return _emit("rescue_sandbox_copy_execution_precheck", _PRECHECK, "blocked", {}, wrote=False, warnings=[], errors=[g0])

    warnings: list[str] = []
    errors: list[str] = []

    fin, fe = load_json_handoff(_SB_FIN, "RESCUE_SCCOPY_SF")
    if fe or not isinstance(fin, dict):
        errors.append("RESCUE_SCCOPY_PC_FIN_MISSING")
    else:
        gs = str(fin.get("gate_status") or "")
        if gs == "blocked":
            errors.append("RESCUE_SCCOPY_PC_FIN_BLOCKED")
        elif gs not in ("ready", "review_required"):
            errors.append("RESCUE_SCCOPY_PC_FIN_NOT_GREEN")

    safe, se = load_json_handoff(_SB_SAFE, "RESCUE_SCCOPY_SS")
    if se or not isinstance(safe, dict):
        errors.append("RESCUE_SCCOPY_PC_SAFE_MISSING")
    else:
        ev = safe.get("evaluation") if isinstance(safe.get("evaluation"), dict) else {}
        ss = str(ev.get("rescue_build_sandbox_safety_eval_status") or "")
        if ss == "blocked":
            errors.append("RESCUE_SCCOPY_PC_SAFE_BLOCKED")
        elif ss not in ("ok", "review_required"):
            errors.append("RESCUE_SCCOPY_PC_SAFE_NOT_GREEN")

    for mf in (_MANIFEST, _CFG_PLAN, _RT_PLAN):
        p, err = _build_path(mf)
        if err or p is None or not p.is_file():
            errors.append(f"RESCUE_SCCOPY_PC_MANIFEST_MISSING:{mf}")

    def _check_entries(entries: list[dict[str, Any]], required_prefix: str, tag: str, *, require_text_suffix: bool) -> None:
        for e in entries[:_MAX_ENTRIES]:
            sp = str(e.get("source_path") or "").replace("\\", "/").strip()
            tp = str(e.get("target_path") or "").replace("\\", "/").strip()
            if not sp or not tp:
                errors.append(f"RESCUE_SCCOPY_PC_EMPTY_PATH:{tag}")
                continue
            if e.get("overwrite_allowed") is True:
                errors.append(f"RESCUE_SCCOPY_PC_OVERWRITE_TRUE:{tag}:{tp}")
                continue
            blk = _path_blocked(sp) or _path_blocked(tp)
            if blk:
                errors.append(f"RESCUE_SCCOPY_PC_BLOCKED_ARTIFACT:{tag}:{blk}")
            if "docs/evidence" in tp or "/history/" in tp or tp.startswith("docs/"):
                errors.append(f"RESCUE_SCCOPY_PC_EVIDENCE_TARGET:{tp}")
            if not tp.startswith(required_prefix):
                errors.append(f"RESCUE_SCCOPY_PC_TARGET_PREFIX:{tp}")
            src = _repo_path(sp)
            if src is None:
                errors.append(f"RESCUE_SCCOPY_PC_SRC_BAD:{sp}")
                continue
            if src.is_symlink():
                try:
                    src.resolve().relative_to(BUILD_RESCUE_ROOT.resolve(strict=False))
                except (OSError, ValueError):
                    errors.append(f"RESCUE_SCCOPY_PC_SYMLINK_ESCAPE:{sp}")
            if not src.is_file():
                if _entry_optional(e):
                    warnings.append(f"RESCUE_SCCOPY_PC_SRC_MISSING_OPT:{sp}")
                else:
                    errors.append(f"RESCUE_SCCOPY_PC_SRC_MISSING:{sp}")
                continue
            try:
                sz = src.stat().st_size
            except OSError:
                errors.append(f"RESCUE_SCCOPY_PC_SRC_STAT:{sp}")
                continue
            if sz > _MAX_COPY_BYTES:
                errors.append(f"RESCUE_SCCOPY_PC_SIZE:{sp}")
            if require_text_suffix and not _is_textish_suffix(src.name):
                errors.append(f"RESCUE_SCCOPY_PC_SUFFIX:{sp}")
            tdest = _repo_path(tp)
            if tdest is None:
                errors.append(f"RESCUE_SCCOPY_PC_TGT_BAD:{tp}")
                continue
            if not _under_sandbox_resolved(tdest):
                errors.append(f"RESCUE_SCCOPY_PC_TGT_OUTSIDE_SB:{tp}")

    ce, cerr = _load_plan(_CFG_PLAN)
    if cerr:
        errors.append(f"RESCUE_SCCOPY_PC_CFG_PLAN:{cerr}")
    else:
        _check_entries(ce or [], _PREFIX_CFG, "cfg", require_text_suffix=True)

    re, rerr = _load_plan(_RT_PLAN)
    if rerr:
        errors.append(f"RESCUE_SCCOPY_PC_RT_PLAN:{rerr}")
    else:
        _check_entries(re or [], _PREFIX_RT, "rt", require_text_suffix=False)

    st = "blocked" if errors else ("review_required" if warnings else "ok")
    body: dict[str, Any] = {
        "rescue_sandbox_copy_execution_precheck_schema_version": 1,
        "strict_mode": "rescue_sandbox_controlled_copy",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "max_copy_bytes": _MAX_COPY_BYTES,
        "precheck_eval_status": st,
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_HANDOFF)
    if werr:
        return _emit("rescue_sandbox_copy_execution_precheck", _PRECHECK, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit("rescue_sandbox_copy_execution_precheck", _PRECHECK, st, body, wrote=True, warnings=warnings, errors=errors)


def _execute_plan_copy(
    *,
    plan_rel: str,
    result_rel: str,
    required_prefix: str,
    tag: str,
    explicit_overwrite: bool,
    require_text_suffix: bool,
) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    rp, rerr = _build_path(result_rel)
    if rerr or rp is None:
        return _emit(f"rescue_sandbox_copy_{tag}", result_rel, "blocked", {}, wrote=False, warnings=[], errors=[rerr or "PATH"])
    g = guard_handoff_overwrite(rp, explicit_overwrite=explicit_overwrite, prefix=f"RESCUE_SCCOPY_{tag.upper()}")
    if g:
        return _emit(f"rescue_sandbox_copy_{tag}", result_rel, "blocked", {}, wrote=False, warnings=[], errors=[g])

    entries, perr = _load_plan(plan_rel)
    if perr or entries is None:
        return _emit(f"rescue_sandbox_copy_{tag}", result_rel, "blocked", {}, wrote=False, warnings=[], errors=[perr or "PLAN"])

    copied: list[dict[str, Any]] = []
    skipped: list[str] = []

    for e in entries[:_MAX_ENTRIES]:
        sp = str(e.get("source_path") or "").replace("\\", "/").strip()
        tp = str(e.get("target_path") or "").replace("\\", "/").strip()
        if not sp or not tp or not tp.startswith(required_prefix):
            errors.append(f"RESCUE_SCCOPY_EX_PATH:{sp}->{tp}")
            continue
        if e.get("overwrite_allowed") is True:
            errors.append(f"RESCUE_SCCOPY_EX_OW:{tp}")
            continue
        blk = _path_blocked(sp) or _path_blocked(tp)
        if blk:
            errors.append(f"RESCUE_SCCOPY_EX_BLK:{blk}:{sp}")
            continue
        if "docs/evidence" in tp or "/history/" in tp:
            errors.append(f"RESCUE_SCCOPY_EX_EV:{tp}")
            continue
        src = _repo_path(sp)
        tgt = _repo_path(tp)
        if src is None or tgt is None:
            errors.append(f"RESCUE_SCCOPY_EX_BAD:{sp}")
            continue
        if not _under_sandbox_resolved(tgt):
            errors.append(f"RESCUE_SCCOPY_EX_OUT:{tp}")
            continue
        if not src.is_file():
            skipped.append(sp)
            continue
        try:
            sz = src.stat().st_size
            data = src.read_bytes()
        except OSError:
            errors.append(f"RESCUE_SCCOPY_EX_READ:{sp}")
            continue
        if sz > _MAX_COPY_BYTES or len(data) > _MAX_COPY_BYTES:
            errors.append(f"RESCUE_SCCOPY_EX_SIZE:{sp}")
            continue
        if _looks_binary(data):
            errors.append(f"RESCUE_SCCOPY_EX_BINARY:{sp}")
            continue
        if require_text_suffix and not _is_textish_suffix(src.name):
            errors.append(f"RESCUE_SCCOPY_EX_SUFFIX:{sp}")
            continue
        if tgt.exists() and tgt.is_file() and not explicit_overwrite:
            errors.append(f"RESCUE_SCCOPY_EX_EXISTS:{tp}")
            continue
        sh_src = _sha256_bytes(data)
        try:
            _atomic_write_bytes(tgt, data)
        except OSError:
            errors.append(f"RESCUE_SCCOPY_EX_WRITE:{tp}")
            continue
        sh_tgt = _sha256_file(tgt)
        if sh_tgt != sh_src:
            errors.append(f"RESCUE_SCCOPY_EX_HASH_POST:{tp}")
        copied.append(
            {
                "source_path": sp,
                "source_sha256": sh_src,
                "target_path": tp,
                "target_sha256": sh_tgt,
            }
        )

    st = "blocked" if errors else ("review_required" if (warnings or skipped) else "ok")
    body: dict[str, Any] = {
        f"{tag}_copy_result_schema_version": 1,
        "copied": copied,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "skipped_sources": skipped,
        "strict_mode": "rescue_sandbox_controlled_copy",
        f"rescue_sandbox_copy_{tag}_status": st,
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_MANIFEST:
        return _emit(f"rescue_sandbox_copy_{tag}", result_rel, "blocked", body, wrote=False, warnings=warnings, errors=["RESCUE_SCCOPY_EX_TOO_LARGE"])
    try:
        atomic_write_text(rp, text)
    except OSError:
        return _emit(f"rescue_sandbox_copy_{tag}", result_rel, "blocked", body, wrote=False, warnings=warnings, errors=["RESCUE_SCCOPY_EX_WRITE_RESULT"])
    return _emit(f"rescue_sandbox_copy_{tag}", result_rel, st, body, wrote=True, warnings=warnings, errors=errors)


def execute_rescue_sandbox_config_copy(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    return _execute_plan_copy(
        plan_rel=_CFG_PLAN,
        result_rel=_CFG_RESULT,
        required_prefix=_PREFIX_CFG,
        tag="config",
        explicit_overwrite=explicit_overwrite,
        require_text_suffix=True,
    )


def execute_rescue_sandbox_runtime_copy(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    return _execute_plan_copy(
        plan_rel=_RT_PLAN,
        result_rel=_RT_RESULT,
        required_prefix=_PREFIX_RT,
        tag="runtime",
        explicit_overwrite=explicit_overwrite,
        require_text_suffix=False,
    )


def _read_copy_rows(rel: str) -> list[dict[str, Any]]:
    p, err = _build_path(rel)
    if err or p is None or not p.is_file():
        return []
    try:
        o = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    rows = o.get("copied") if isinstance(o.get("copied"), list) else []
    return [x for x in rows if isinstance(x, dict)]


def _verify_plan_rows(
    plan_rel: str,
    required_prefix: str,
    copied_rows: list[dict[str, Any]],
    *,
    warnings: list[str],
    errors: list[str],
) -> None:
    entries, perr = _load_plan(plan_rel)
    if perr or entries is None:
        errors.append(f"RESCUE_SCCOPY_V_PLAN:{plan_rel}:{perr}")
        return
    copied_tp = {str(r.get("target_path") or "").replace("\\", "/") for r in copied_rows}
    for e in entries[:_MAX_ENTRIES]:
        if not isinstance(e, dict):
            continue
        tp = str(e.get("target_path") or "").replace("\\", "/").strip()
        if not tp.startswith(required_prefix):
            continue
        if tp in copied_tp:
            continue
        if _entry_optional(e):
            warnings.append(f"RESCUE_SCCOPY_V_OPT_NOT_COPIED:{tp}")
        else:
            errors.append(f"RESCUE_SCCOPY_V_PLAN_NOT_COPIED:{tp}")


def verify_rescue_sandbox_copy_results(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_VERIFY, "RESCUE_SCCOPY_V")
    if oerr or out_path is None:
        return _emit("rescue_sandbox_copy_verify", _VERIFY, "blocked", {}, wrote=False, warnings=[], errors=[oerr or "INVALID"])
    g0 = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_SCCOPY_V")
    if g0:
        return _emit("rescue_sandbox_copy_verify", _VERIFY, "blocked", {}, wrote=False, warnings=[], errors=[g0])

    warnings: list[str] = []
    errors: list[str] = []

    expected: set[str] = set()
    cfg_rows = _read_copy_rows(_CFG_RESULT)
    rt_rows = _read_copy_rows(_RT_RESULT)
    _verify_plan_rows(_CFG_PLAN, _PREFIX_CFG, cfg_rows, warnings=warnings, errors=errors)
    _verify_plan_rows(_RT_PLAN, _PREFIX_RT, rt_rows, warnings=warnings, errors=errors)

    def _consume_result(rel: str) -> None:
        p, err = _build_path(rel)
        if err or p is None or not p.is_file():
            errors.append(f"RESCUE_SCCOPY_V_MISSING:{rel}")
            return
        try:
            o = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            errors.append(f"RESCUE_SCCOPY_V_JSON:{rel}")
            return
        for row in o.get("copied") or []:
            if not isinstance(row, dict):
                continue
            tp = str(row.get("target_path") or "").replace("\\", "/")
            expected.add(tp)
            ss = str(row.get("source_sha256") or "")
            ts = str(row.get("target_sha256") or "")
            tfp = _repo_path(tp)
            if tfp is None:
                errors.append(f"RESCUE_SCCOPY_V_NOFILE:{tp}")
                continue
            if tfp.is_symlink():
                errors.append(f"RESCUE_SCCOPY_V_SYMLINK:{tp}")
                continue
            if not tfp.is_file():
                errors.append(f"RESCUE_SCCOPY_V_NOFILE:{tp}")
                continue
            if not _under_sandbox_resolved(tfp):
                errors.append(f"RESCUE_SCCOPY_V_ESCAPE:{tp}")
                continue
            act = _sha256_file(tfp)
            if act != ss or act != ts or ss != ts:
                errors.append(f"RESCUE_SCCOPY_V_HASH:{tp}")
            try:
                raw = tfp.read_text(encoding="utf-8", errors="replace")
            except OSError:
                errors.append(f"RESCUE_SCCOPY_V_READ:{tp}")
                continue
            if _LEGACY_PI.search(raw):
                errors.append(f"RESCUE_SCCOPY_V_LEGACY:{tp}")
            blk = _path_blocked(tp)
            if blk:
                errors.append(f"RESCUE_SCCOPY_V_BADNAME:{tp}")

    _consume_result(_CFG_RESULT)
    _consume_result(_RT_RESULT)

    sb_root = (BUILD_RESCUE_ROOT / "sandbox").resolve(strict=False)
    for sub, _pfx in (("config-copy", _PREFIX_CFG), ("runtime-copy", _PREFIX_RT)):
        root = sb_root / sub
        if not root.is_dir():
            continue
        for fp in root.rglob("*"):
            if fp.is_symlink():
                try:
                    rels = fp.relative_to(REPO_ROOT).as_posix()
                except ValueError:
                    rels = str(fp)
                errors.append(f"RESCUE_SCCOPY_V_SYMLINK_DIR:{rels}")
                continue
            if not fp.is_file():
                continue
            try:
                rel = fp.relative_to(REPO_ROOT).as_posix()
            except ValueError:
                continue
            norm = rel.replace("\\", "/")
            if norm not in expected:
                errors.append(f"RESCUE_SCCOPY_V_UNEXPECTED:{norm}")

    st = "blocked" if errors else ("review_required" if warnings else "ok")
    body: dict[str, Any] = {
        "rescue_sandbox_copy_verify_result_schema_version": 1,
        "expected_targets_count": len(expected),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "strict_mode": "rescue_sandbox_controlled_copy",
        "verify_eval_status": st,
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_HANDOFF)
    if werr:
        return _emit("rescue_sandbox_copy_verify", _VERIFY, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit("rescue_sandbox_copy_verify", _VERIFY, st, body, wrote=True, warnings=warnings, errors=errors)


def build_rescue_sandbox_copy_seal(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    sp, serr = _build_path(_SEAL)
    if serr or sp is None:
        return _emit("rescue_sandbox_copy_seal", _SEAL, "blocked", {}, wrote=False, warnings=[], errors=[serr or "PATH"])
    g = guard_handoff_overwrite(sp, explicit_overwrite=explicit_overwrite, prefix="RESCUE_SCCOPY_SEAL")
    if g:
        return _emit("rescue_sandbox_copy_seal", _SEAL, "blocked", {}, wrote=False, warnings=[], errors=[g])

    vp, ve = resolve_handoff_path(_VERIFY, "RESCUE_SCCOPY_V2")
    if ve or vp is None or not vp.is_file():
        return _emit(
            "rescue_sandbox_copy_seal",
            _SEAL,
            "blocked",
            {},
            wrote=False,
            warnings=[],
            errors=["RESCUE_SCCOPY_SEAL_VERIFY_MISSING"],
        )
    try:
        vo = json.loads(vp.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _emit(
            "rescue_sandbox_copy_seal",
            _SEAL,
            "blocked",
            {},
            wrote=False,
            warnings=[],
            errors=["RESCUE_SCCOPY_SEAL_VERIFY_JSON"],
        )
    vs = str(vo.get("verify_eval_status") or "")
    if vs == "blocked":
        return _emit(
            "rescue_sandbox_copy_seal",
            _SEAL,
            "blocked",
            {"verify_eval_status": vs},
            wrote=False,
            warnings=[],
            errors=["RESCUE_SCCOPY_SEAL_VERIFY_BLOCKED"],
        )
    if vs not in ("ok", "review_required"):
        return _emit(
            "rescue_sandbox_copy_seal",
            _SEAL,
            "blocked",
            {"verify_eval_status": vs},
            wrote=False,
            warnings=[],
            errors=["RESCUE_SCCOPY_SEAL_VERIFY_NOT_GREEN"],
        )

    hashes: dict[str, str] = {}
    for label, rel in (
        ("config_copy_result_sha256", _CFG_RESULT),
        ("runtime_copy_result_sha256", _RT_RESULT),
    ):
        p, err = _build_path(rel)
        if err or p is None or not p.is_file():
            warnings.append(f"RESCUE_SCCOPY_SEAL_MISSING:{rel}")
            continue
        try:
            raw = p.read_bytes()
        except OSError:
            errors.append(f"RESCUE_SCCOPY_SEAL_READ:{rel}")
            continue
        hashes[label] = _sha256_bytes(raw)

    try:
        vraw = vp.read_bytes()
        hashes["verify_result_handoff_sha256"] = _sha256_bytes(vraw)
    except OSError:
        errors.append("RESCUE_SCCOPY_SEAL_VERIFY_READ")

    seal_st = "blocked" if errors else ("review_required" if warnings else "ok")
    body: dict[str, Any] = {
        "sandbox_copy_seal_schema_version": 1,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hashes": hashes,
        "rescue_sandbox_copy_seal_status": seal_st,
        "seal_status": seal_st,
        "strict_mode": "rescue_sandbox_controlled_copy",
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_MANIFEST:
        return _emit("rescue_sandbox_copy_seal", _SEAL, "blocked", body, wrote=False, warnings=warnings, errors=["RESCUE_SCCOPY_SEAL_TOO_LARGE"])
    if seal_st == "blocked":
        return _emit("rescue_sandbox_copy_seal", _SEAL, seal_st, body, wrote=False, warnings=warnings, errors=errors)
    try:
        atomic_write_text(sp, text)
    except OSError:
        return _emit("rescue_sandbox_copy_seal", _SEAL, "blocked", body, wrote=False, warnings=warnings, errors=["RESCUE_SCCOPY_SEAL_WRITE"])
    return _emit("rescue_sandbox_copy_seal", _SEAL, seal_st, body, wrote=True, warnings=warnings, errors=errors)


def build_rescue_sandbox_copy_final_gate(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_COPY_FIN, "RESCUE_SCCOPY_FG")
    if oerr or out_path is None:
        return _emit("rescue_sandbox_copy_final_gate", _COPY_FIN, "blocked", {}, wrote=False, warnings=[], errors=[oerr or "INVALID"])
    g0 = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_SCCOPY_FG")
    if g0:
        return _emit("rescue_sandbox_copy_final_gate", _COPY_FIN, "blocked", {}, wrote=False, warnings=[], errors=[g0])

    warnings: list[str] = []
    errors: list[str] = []

    inputs: dict[str, str] = {
        "copy_execution_precheck": _PRECHECK,
        "config_copy_result": _CFG_RESULT,
        "runtime_copy_result": _RT_RESULT,
        "copy_verify_result": _VERIFY,
        "sandbox_copy_seal": _SEAL,
        "branding_guard": _BRAND,
        "zero_state_verification": _ZERO,
    }

    for key, rel in inputs.items():
        if key in ("branding_guard", "zero_state_verification"):
            continue
        if key == "copy_execution_precheck" or key == "copy_verify_result":
            p, e = resolve_handoff_path(rel, "RESCUE_SCCOPY_FG2")
            if e or p is None or not p.is_file():
                errors.append(f"RESCUE_SCCOPY_FG_MISSING:{rel}")
        else:
            p, e = _build_path(rel)
            if e or p is None or not p.is_file():
                errors.append(f"RESCUE_SCCOPY_FG_MISSING:{rel}")

    pc, pce = load_json_handoff(_PRECHECK, "RESCUE_SCCOPY_PC3")
    if pce or not isinstance(pc, dict):
        errors.append("RESCUE_SCCOPY_FG_PC_MISSING")
    elif str(pc.get("precheck_eval_status") or "") == "blocked":
        errors.append("RESCUE_SCCOPY_FG_PC_BLOCKED")
    elif str(pc.get("precheck_eval_status") or "") != "ok":
        warnings.append("RESCUE_SCCOPY_FG_PC_REVIEW")

    vv, vve = load_json_handoff(_VERIFY, "RESCUE_SCCOPY_V3")
    if vve or not isinstance(vv, dict):
        errors.append("RESCUE_SCCOPY_FG_VERIFY_MISSING")
    else:
        vvs = str(vv.get("verify_eval_status") or "")
        if vvs == "blocked":
            errors.append("RESCUE_SCCOPY_FG_VERIFY_BLOCKED")
        elif vvs != "ok":
            warnings.append("RESCUE_SCCOPY_FG_VERIFY_REVIEW")

    seal, se = _build_path(_SEAL)
    if se or seal is None or not seal.is_file():
        errors.append("RESCUE_SCCOPY_FG_SEAL_MISSING")
    else:
        try:
            so = json.loads(seal.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            errors.append("RESCUE_SCCOPY_FG_SEAL_JSON")
            so = {}
        ss = str(so.get("seal_status") or "")
        if ss == "blocked":
            errors.append("RESCUE_SCCOPY_FG_SEAL_BLOCKED")
        elif ss != "ok":
            warnings.append("RESCUE_SCCOPY_FG_SEAL_REVIEW")

    brand, _ = load_json_handoff(_BRAND, "RESCUE_SCCOPY_BR")
    if isinstance(brand, dict) and str(brand.get("branding_guard_status") or "") == "blocked":
        errors.append("RESCUE_SCCOPY_FG_BRAND")

    zero, ze = load_json_handoff(_ZERO, "RESCUE_SCCOPY_ZE")
    if ze:
        warnings.append(f"RESCUE_SCCOPY_FG_ZERO:{ze}")
    elif isinstance(zero, dict) and str(zero.get("zero_state_status") or "") == "blocked":
        errors.append("RESCUE_SCCOPY_FG_ZERO_BLOCKED")

    for rel in (_CFG_RESULT, _RT_RESULT):
        p, _ = _build_path(rel)
        if p and p.is_file():
            try:
                raw = p.read_text(encoding="utf-8")
                if _LEGACY_PI.search(raw):
                    errors.append(f"RESCUE_SCCOPY_FG_LEGACY:{rel}")
            except OSError:
                errors.append(f"RESCUE_SCCOPY_FG_READ:{rel}")

    gst = "ready"
    if errors:
        gst = "blocked"
    elif warnings:
        gst = "review_required"

    body: dict[str, Any] = {
        "gate_status": gst,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "inputs": inputs,
        "rescue_sandbox_copy_final_gate_schema_version": 1,
        "strict_mode": "rescue_sandbox_controlled_copy",
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_HANDOFF)
    if werr:
        return _emit("rescue_sandbox_copy_final_gate", _COPY_FIN, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit("rescue_sandbox_copy_final_gate", _COPY_FIN, gst, body, wrote=True, warnings=warnings, errors=errors)
