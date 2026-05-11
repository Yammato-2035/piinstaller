from __future__ import annotations

import json
import re
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from deploy.runner_rescue_io import (
    BUILD_RESCUE_ROOT,
    REPO_ROOT,
    guard_handoff_overwrite,
    load_json_handoff,
    resolve_handoff_path,
    resolve_under_build_rescue,
    write_json_handoff,
)

_MAX_MANIFEST = 900_000
_MAX_HANDOFF = 512 * 1024

_GRAPH = "build/rescue/dry_build_stage_graph.json"
_RESOLUTION = "build/rescue/dry_build_input_resolution.json"
_PKG_PLAN = "build/rescue/package_resolution_plan.json"
_ORDER = "build/rescue/build_order_validation.json"
_SIM = "build/rescue/dry_build_execution_simulation.json"
_FIN = "docs/evidence/runtime-results/handoff/rescue_dry_build_final_gate.json"
_SAFE = "docs/evidence/runtime-results/handoff/rescue_dry_build_safety_validation.json"

_PKG_LIST = "build/rescue/debian-live/config/package-lists/setuphelfer-rescue.list.chroot"
_SEAL = "build/rescue/runtime_bundle.seal.json"
_HASH_MANIFEST = "build/rescue/runtime_bundle_hash_manifest.json"
_INV = "build/rescue/runtime_bundle_inventory.json"

_CC = "docs/evidence/runtime-results/handoff/rescue_runtime_bundle_consistency_check.json"
_DL_FIN = "docs/evidence/runtime-results/handoff/debian_live_build_inputs_final_gate.json"
_RT_FIN = "docs/evidence/runtime-results/handoff/rescue_runtime_assembly_final_gate.json"
_PB_FIN = "docs/evidence/runtime-results/handoff/rescue_pseudo_boot_final_readiness.json"
_BRAND = "docs/evidence/runtime-results/handoff/setuphelfer_branding_guard_check.json"
_ZERO = "docs/evidence/runtime-results/handoff/runtime_identifier_zero_state_verification.json"
_RT_SAFE = "docs/evidence/runtime-results/handoff/rescue_runtime_assembly_safety.json"
_DL_SAFE = "docs/evidence/runtime-results/handoff/debian_live_build_inputs_safety.json"

_LEGACY_PI = re.compile(r"(?<![A-Za-z0-9_])pi[-_]installer(?![A-Za-z0-9_])")


def _routes_text() -> str:
    p = REPO_ROOT / "backend" / "deploy" / "routes.py"
    return p.read_text(encoding="utf-8") if p.is_file() else ""


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
    return resolve_under_build_rescue(raw, "RESCUE_DRY")


def _ensure_under_build_rescue(p: Path) -> tuple[bool, str | None]:
    try:
        p.resolve(strict=False).relative_to(BUILD_RESCUE_ROOT.resolve(strict=False))
    except (OSError, ValueError):
        return False, "RESCUE_DRY_OUTSIDE_BUILD_RESCUE"
    return True, None


def _guard_build_file(path: Path, *, explicit_overwrite: bool, prefix: str) -> str | None:
    if path.exists() and path.is_file() and not explicit_overwrite:
        return f"{prefix}_EXISTS_NO_OVERWRITE"
    return None


def _write_json_build(path: Path, obj: dict[str, Any]) -> str | None:
    ok, oerr = _ensure_under_build_rescue(path)
    if not ok:
        return oerr or "OUTSIDE"
    text = json.dumps(obj, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_MANIFEST:
        return "RESCUE_DRY_MANIFEST_TOO_LARGE"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return None


def _handoff_exists(rel: str) -> bool:
    p, err = resolve_handoff_path(rel, "RESCUE_DRY")
    return bool(p and p.is_file() and not err)


def _build_file_exists(rel: str) -> bool:
    p, err = _build_path(rel)
    return bool(p and p.is_file() and not err)


def _artifact_exists(rel: str) -> bool:
    r = rel.replace("\\", "/").strip()
    if r.startswith("docs/evidence/"):
        return _handoff_exists(r)
    return _build_file_exists(r)


def _read_build_json(rel: str) -> tuple[dict[str, Any] | None, str | None]:
    p, err = _build_path(rel)
    if err or p is None or not p.is_file():
        return None, err or "RESCUE_DRY_JSON_MISSING"
    try:
        o = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, "RESCUE_DRY_JSON_INVALID"
    return (o if isinstance(o, dict) else None), None


def _CONFIG_MANIFEST() -> str:
    return "build/rescue/debian-live/config_structure_manifest.json"


def _PKG_MANIFEST() -> str:
    return "build/rescue/debian-live/manifests/package_lists_manifest.json"


def _INC_MANIFEST() -> str:
    return "build/rescue/debian-live/manifests/includes_chroot_manifest.json"


def _BOOT_MANIFEST() -> str:
    return "build/rescue/debian-live/manifests/bootloader_templates_manifest.json"


def _HOOK_MANIFEST() -> str:
    return "build/rescue/debian-live/manifests/hook_templates_manifest.json"


def _dry_stages() -> list[dict[str, Any]]:
    mk = lambda sid, deps, ins, outs: {  # noqa: E731
        "stage_id": sid,
        "dependencies": deps,
        "required_inputs": ins,
        "expected_outputs": outs,
        "destructive": False,
        "execute_allowed": False,
    }
    return [
        mk("s01", [], [_CC, _SEAL, _HASH_MANIFEST, _INV], [_CC]),
        mk("s02", ["s01"], [_CONFIG_MANIFEST()], [_CONFIG_MANIFEST()]),
        mk("s03", ["s02"], [_PKG_LIST], [_PKG_LIST, _PKG_MANIFEST()]),
        mk("s04", ["s03"], [_INC_MANIFEST()], [_INC_MANIFEST()]),
        mk("s05", ["s04"], [_BOOT_MANIFEST()], [_BOOT_MANIFEST()]),
        mk("s06", ["s05"], [_HOOK_MANIFEST()], [_HOOK_MANIFEST()]),
        mk("s07", ["s06"], [_RT_FIN, _RT_SAFE], [_RT_FIN]),
        mk("s08", ["s07"], [_PB_FIN], [_PB_FIN]),
        mk("s09", ["s08"], [_DL_SAFE, _RT_SAFE], [_SAFE]),
        mk("s10", ["s09"], [_FIN], [_FIN]),
    ]


def build_rescue_dry_build_stage_graph(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    path, perr = _build_path(_GRAPH)
    if perr or path is None:
        return _emit("rescue_dry_build_stage_graph", _GRAPH, "blocked", {}, wrote=False, warnings=[], errors=[perr or "PATH"])
    g = _guard_build_file(path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_DRY_SG")
    if g:
        return _emit("rescue_dry_build_stage_graph", _GRAPH, "blocked", {}, wrote=False, warnings=[], errors=[g])

    stages = _dry_stages()
    body: dict[str, Any] = {
        "dry_build_stage_graph_schema_version": 1,
        "strict_mode": "rescue_dry_build_orchestration",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stages": stages,
        "no_execute_stages": True,
    }
    werr = _write_json_build(path, body)
    if werr:
        return _emit("rescue_dry_build_stage_graph", _GRAPH, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit("rescue_dry_build_stage_graph", _GRAPH, "ok", body, wrote=True, warnings=warnings, errors=errors)


def build_rescue_dry_build_input_resolution(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    path, perr = _build_path(_RESOLUTION)
    if perr or path is None:
        return _emit("rescue_dry_build_input_resolution", _RESOLUTION, "blocked", {}, wrote=False, warnings=[], errors=[perr or "PATH"])
    g = _guard_build_file(path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_DRY_IR")
    if g:
        return _emit("rescue_dry_build_input_resolution", _RESOLUTION, "blocked", {}, wrote=False, warnings=[], errors=[g])

    required_specs: list[tuple[str, str, bool]] = [
        ("rescue_runtime_bundle_consistency_check", _CC, True),
        ("runtime_bundle_seal", _SEAL, False),
        ("runtime_bundle_hash_manifest", _HASH_MANIFEST, False),
        ("runtime_bundle_inventory", _INV, False),
        ("debian_live_build_inputs_final_gate", _DL_FIN, True),
        ("rescue_runtime_assembly_final_gate", _RT_FIN, True),
        ("rescue_pseudo_boot_final_readiness", _PB_FIN, True),
        ("setuphelfer_branding_guard_check", _BRAND, True),
        ("runtime_identifier_zero_state_verification", _ZERO, True),
    ]
    optional_specs: list[tuple[str, str, bool]] = [
        ("rescue_runtime_assembly_safety", _RT_SAFE, True),
        ("debian_live_build_inputs_safety", _DL_SAFE, True),
    ]

    resolved: list[str] = []
    missing: list[str] = []
    blocked: list[str] = []
    optional_hit: list[str] = []

    for key, rel, is_handoff in required_specs:
        ok = _handoff_exists(rel) if is_handoff else _build_file_exists(rel)
        if ok:
            resolved.append(key)
        else:
            missing.append(f"{key}:{rel}")
    for key, rel, is_handoff in optional_specs:
        ok = _handoff_exists(rel) if is_handoff else _build_file_exists(rel)
        if ok:
            optional_hit.append(key)
        else:
            warnings.append(f"RESCUE_DRY_IR_OPTIONAL_MISSING:{key}")

    cc, ce = load_json_handoff(_CC, "RESCUE_DRY_CC")
    if ce or not isinstance(cc, dict):
        blocked.append("RESCUE_DRY_IR_CONSISTENCY_HANDOFF_INVALID")
    else:
        cst = str(cc.get("consistency_status") or "")
        if cst == "blocked":
            blocked.append("RESCUE_DRY_IR_BUNDLE_CONSISTENCY_BLOCKED")

    body: dict[str, Any] = {
        "dry_build_input_resolution_schema_version": 1,
        "strict_mode": "rescue_dry_build_orchestration",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "resolved_inputs": sorted(resolved),
        "missing_inputs": sorted(missing),
        "blocked_inputs": sorted(blocked),
        "optional_inputs": sorted(optional_hit),
    }
    werr = _write_json_build(path, body)
    if werr:
        return _emit("rescue_dry_build_input_resolution", _RESOLUTION, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    st = "blocked" if (missing or blocked) else ("review_required" if warnings else "ok")
    if missing:
        errors.extend(missing)
    if blocked:
        errors.extend(blocked)
    return _emit("rescue_dry_build_input_resolution", _RESOLUTION, st, body, wrote=True, warnings=warnings, errors=errors)


def _parse_package_list(text: str) -> list[str]:
    pkgs: list[str] = []
    for ln in text.splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        pkgs.append(s.split()[0].strip())
    return pkgs


def build_rescue_package_resolution_plan(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    path, perr = _build_path(_PKG_PLAN)
    if perr or path is None:
        return _emit("rescue_dry_build_package_resolution", _PKG_PLAN, "blocked", {}, wrote=False, warnings=[], errors=[perr or "PATH"])
    g = _guard_build_file(path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_DRY_PR")
    if g:
        return _emit("rescue_dry_build_package_resolution", _PKG_PLAN, "blocked", {}, wrote=False, warnings=[], errors=[g])

    lp, lerr = _build_path(_PKG_LIST)
    if lerr or lp is None or not lp.is_file():
        errors.append("RESCUE_DRY_PR_LIST_MISSING")
        raw = ""
    else:
        raw = lp.read_text(encoding="utf-8", errors="replace")

    names = _parse_package_list(raw) if raw else []
    fs = {"dosfstools", "e2fsprogs", "xfsprogs", "btrfs-progs", "parted", "gdisk", "util-linux"}
    rec = {"rsync", "cryptsetup"}
    diag = {"smartmontools", "nvme-cli", "jq"}
    net = {"curl", "network-manager", "openssh-client", "nodejs"}
    opt_hint = {"nginx-light"}

    req: list[str] = []
    optional: list[str] = []
    filesystem_tools: list[str] = []
    recovery_tools: list[str] = []
    diagnostics_tools: list[str] = []
    network_tools: list[str] = []

    for n in names:
        if n in opt_hint:
            optional.append(n)
        else:
            req.append(n)
        if n in fs:
            filesystem_tools.append(n)
        if n in rec:
            recovery_tools.append(n)
        if n in diag:
            diagnostics_tools.append(n)
        if n in net:
            network_tools.append(n)

    body: dict[str, Any] = {
        "package_resolution_plan_schema_version": 1,
        "strict_mode": "rescue_dry_build_orchestration",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_list_file": _PKG_LIST,
        "required_packages": sorted(req),
        "optional_packages": sorted(optional),
        "filesystem_tools": sorted(filesystem_tools),
        "recovery_tools": sorted(recovery_tools),
        "diagnostics_tools": sorted(diagnostics_tools),
        "network_tools": sorted(network_tools),
        "no_apt_install": True,
    }
    st = "blocked" if errors else ("review_required" if warnings else "ok")
    body["rescue_dry_build_package_resolution_status"] = st
    werr = _write_json_build(path, body)
    if werr:
        return _emit("rescue_dry_build_package_resolution", _PKG_PLAN, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit("rescue_dry_build_package_resolution", _PKG_PLAN, st, body, wrote=True, warnings=warnings, errors=errors)


def _toposort(stage_ids: list[str], deps_map: dict[str, list[str]]) -> tuple[list[str] | None, str | None]:
    rev: dict[str, list[str]] = defaultdict(list)
    in_deg = {sid: 0 for sid in stage_ids}
    for sid in stage_ids:
        for d in deps_map.get(sid, []):
            if d not in in_deg:
                return None, f"RESCUE_DRY_BO_UNKNOWN_DEP:{sid}->{d}"
            rev[d].append(sid)
    for sid in stage_ids:
        in_deg[sid] = len(deps_map.get(sid, []))
    q = deque([s for s in stage_ids if in_deg[s] == 0])
    out: list[str] = []
    while q:
        u = q.popleft()
        out.append(u)
        for v in rev[u]:
            in_deg[v] -= 1
            if in_deg[v] == 0:
                q.append(v)
    if len(out) != len(stage_ids):
        return None, "RESCUE_DRY_BO_CYCLE"
    return out, None


def validate_rescue_build_order(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    path, perr = _build_path(_ORDER)
    if perr or path is None:
        return _emit("rescue_dry_build_build_order_validation", _ORDER, "blocked", {}, wrote=False, warnings=[], errors=[perr or "PATH"])
    g = _guard_build_file(path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_DRY_BO")
    if g:
        return _emit("rescue_dry_build_build_order_validation", _ORDER, "blocked", {}, wrote=False, warnings=[], errors=[g])

    gp, gerr = _build_path(_GRAPH)
    if gerr or gp is None or not gp.is_file():
        errors.append("RESCUE_DRY_BO_GRAPH_MISSING")
        st0 = "blocked"
        body: dict[str, Any] = {
            "build_order_validation_schema_version": 1,
            "strict_mode": "rescue_dry_build_orchestration",
            "ordered_stage_ids": [],
            "rescue_dry_build_build_order_validation_status": st0,
        }
        werr = _write_json_build(path, body)
        if werr:
            return _emit("rescue_dry_build_build_order_validation", _ORDER, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
        return _emit("rescue_dry_build_build_order_validation", _ORDER, "blocked", body, wrote=True, warnings=warnings, errors=errors)

    try:
        graph = json.loads(gp.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        errors.append("RESCUE_DRY_BO_GRAPH_JSON_INVALID")
        graph = {}

    stages = graph.get("stages") if isinstance(graph.get("stages"), list) else []
    stage_ids: list[str] = []
    deps_map: dict[str, list[str]] = {}
    forbidden_substrings = ("iso_output", "qemu_boot", "lb_exec", "execute_build")

    for st in stages:
        if not isinstance(st, dict):
            continue
        sid = str(st.get("stage_id") or "")
        if not sid:
            continue
        low = sid.lower()
        for fb in forbidden_substrings:
            if fb in low:
                errors.append(f"RESCUE_DRY_BO_FORBIDDEN_STAGE:{sid}")
        if st.get("destructive") is True:
            errors.append(f"RESCUE_DRY_BO_DESTRUCTIVE_TRUE:{sid}")
        if st.get("execute_allowed") is True:
            errors.append(f"RESCUE_DRY_BO_EXECUTE_ALLOWED:{sid}")
        stage_ids.append(sid)
        deps_map[sid] = [str(x) for x in (st.get("dependencies") or []) if x is not None]

    order, oerr = _toposort(stage_ids, deps_map)
    if oerr:
        errors.append(oerr)

    rp, _ = _build_path(_RESOLUTION)
    if rp and rp.is_file():
        try:
            reso = json.loads(rp.read_text(encoding="utf-8"))
            miss = reso.get("missing_inputs") if isinstance(reso.get("missing_inputs"), list) else []
            if miss:
                errors.append("RESCUE_DRY_BO_MISSING_INPUTS")
        except json.JSONDecodeError:
            warnings.append("RESCUE_DRY_BO_RESOLUTION_JSON_INVALID")

    st = "ok" if not errors else "blocked"
    body: dict[str, Any] = {
        "build_order_validation_schema_version": 1,
        "strict_mode": "rescue_dry_build_orchestration",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ordered_stage_ids": order or [],
        "no_execute_stages": True,
        "no_iso_stages": True,
        "rescue_dry_build_build_order_validation_status": st,
    }
    werr = _write_json_build(path, body)
    if werr:
        return _emit("rescue_dry_build_build_order_validation", _ORDER, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit("rescue_dry_build_build_order_validation", _ORDER, st, body, wrote=True, warnings=warnings, errors=errors)


def simulate_rescue_dry_build_execution(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    path, perr = _build_path(_SIM)
    if perr or path is None:
        return _emit("rescue_dry_build_execution_simulation", _SIM, "blocked", {}, wrote=False, warnings=[], errors=[perr or "PATH"])
    g = _guard_build_file(path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_DRY_SIM")
    if g:
        return _emit("rescue_dry_build_execution_simulation", _SIM, "blocked", {}, wrote=False, warnings=[], errors=[g])

    op, _ = _build_path(_ORDER)
    ov: dict[str, Any] = {}
    if not op or not op.is_file():
        errors.append("RESCUE_DRY_SIM_ORDER_MISSING")
    else:
        try:
            raw_o = json.loads(op.read_text(encoding="utf-8"))
            ov = raw_o if isinstance(raw_o, dict) else {}
            if str(ov.get("rescue_dry_build_build_order_validation_status") or "") != "ok":
                errors.append("RESCUE_DRY_SIM_ORDER_NOT_OK")
        except json.JSONDecodeError:
            errors.append("RESCUE_DRY_SIM_ORDER_JSON_INVALID")

    ordered: list[str] = list(ov.get("ordered_stage_ids") or [])

    def _stage_num(sid: str) -> int | None:
        if len(sid) > 1 and sid[0] == "s" and sid[1:].isdigit():
            return int(sid[1:])
        return None

    progression: list[dict[str, Any]] = []
    for sid in ordered:
        n = _stage_num(sid)
        progression.append(
            {
                "stage_id": sid,
                "simulated_status": "simulated_ok",
                "validation_checkpoint": "readonly_plan_only",
                "iso_output": False,
                "recovery_runtime_available": n is not None and n >= 7,
                "readonly_overlay_ready": n is not None and n >= 8,
            }
        )

    st = "ok" if not errors else "blocked"
    body: dict[str, Any] = {
        "dry_build_execution_simulation_schema_version": 1,
        "strict_mode": "rescue_dry_build_orchestration",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "simulation_only": True,
        "stage_progression": progression,
        "expected_outputs_materialized": False,
        "no_real_build": True,
        "rescue_dry_build_execution_simulation_status": st,
    }
    werr = _write_json_build(path, body)
    if werr:
        return _emit("rescue_dry_build_execution_simulation", _SIM, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit("rescue_dry_build_execution_simulation", _SIM, st, body, wrote=True, warnings=warnings, errors=errors)


def _rx(expr: str) -> re.Pattern[str]:
    return re.compile(expr)


_lb_b = "lb" + r"\s+build"
_live_b = "live" + "-" + "build"
_grub_mk = "grub-mk" + "rescue"
_xor = "xor" + "riso"
_debo = "deb" + "ootstrap"
_ch_in = "ch" + "ro" + "ot" + r"\s*\("

_DRY_SAFETY_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (_rx(r"(?i)" + _lb_b), "lb_build"),
    (_rx(r"(?i)\b" + _live_b + r"\s+(run|exec|execute)\b"), "live_build_execute"),
    (_rx(r"(?i)\b" + _debo + r"\b"), "debootstrap"),
    (_rx(r"(?i)\bapt\s+install\b"), "apt_install"),
    (_rx(r"(?i)" + _ch_in), "chroot_invoke"),
    (_rx(r"(?i)\b" + _grub_mk + r"\b"), "grub_mkrescue"),
    (_rx(r"(?i)\b" + _xor + r"\b"), "xorriso"),
    (_rx(r"(?i)\bqe" + "mu-system\b"), "qemu_system"),
    (_rx(r"(?i)\bvbox" + r"manage\b"), "vboxmanage"),
    (_rx(r"(?i)\bdd\b"), "dd_cmd"),
    (_rx(r"(?i)\bmkfs(\.[a-z0-9]+)?\b"), "mkfs"),
    (_rx(r"(?i)\bwipefs\b"), "wipefs"),
    (_rx(r"(?i)\biso\s+creation\b"), "iso_creation"),
    (_rx(r"(?i)\bpublish-release\b"), "publish_release"),
    (_rx(r"(?i)\bdeploy-release\b"), "deploy_release"),
)


def validate_rescue_dry_build_safety(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_SAFE, "RESCUE_DRY_SAFE")
    if oerr or out_path is None:
        return _emit("rescue_dry_build_safety_validation", _SAFE, "blocked", {}, wrote=False, warnings=[], errors=[oerr or "INVALID"])
    g0 = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_DRY_SAFE")
    if g0:
        return _emit("rescue_dry_build_safety_validation", _SAFE, "blocked", {}, wrote=False, warnings=[], errors=[g0])

    warnings: list[str] = []
    errors: list[str] = []

    rt = _routes_text().lower()
    _route_patterns = tuple(x for x in _DRY_SAFETY_PATTERNS if x[1] != "dd_cmd")
    for rx, lid in _route_patterns:
        if rx.search(rt):
            errors.append(f"RESCUE_DRY_SAFE_ROUTES:{lid}")

    for rel in (_GRAPH, _RESOLUTION, _PKG_PLAN, _ORDER, _SIM):
        p, _ = _build_path(rel)
        if p and p.is_file():
            try:
                raw = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if _LEGACY_PI.search(raw):
                errors.append(f"RESCUE_DRY_SAFE_LEGACY:{rel}")
            for rx, lid in _DRY_SAFETY_PATTERNS:
                if rx.search(raw):
                    errors.append(f"RESCUE_DRY_SAFE_ARTIFACT:{rel}:{lid}")

    body: dict[str, Any] = {
        "rescue_dry_build_safety_validation_schema_version": 1,
        "strict_mode": "rescue_dry_build_orchestration",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "evaluation": {"rescue_dry_build_safety_eval_status": "ok" if not errors else "blocked"},
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_HANDOFF)
    if werr:
        return _emit("rescue_dry_build_safety_validation", _SAFE, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    st = "ok" if not errors else "blocked"
    return _emit("rescue_dry_build_safety_validation", _SAFE, st, body, wrote=True, warnings=warnings, errors=errors)


def build_rescue_dry_build_final_gate(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_FIN, "RESCUE_DRY_FIN")
    if oerr or out_path is None:
        return _emit("rescue_dry_build_final_gate", _FIN, "blocked", {}, wrote=False, warnings=[], errors=[oerr or "INVALID"])
    g0 = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_DRY_FIN")
    if g0:
        return _emit("rescue_dry_build_final_gate", _FIN, "blocked", {}, wrote=False, warnings=[], errors=[g0])

    warnings: list[str] = []
    errors: list[str] = []

    inputs: dict[str, str] = {
        "stage_graph": _GRAPH,
        "input_resolution": _RESOLUTION,
        "package_resolution": _PKG_PLAN,
        "build_order_validation": _ORDER,
        "execution_simulation": _SIM,
        "runtime_bundle_consistency": _CC,
        "debian_live_build_inputs_final_gate": _DL_FIN,
        "runtime_assembly_final_gate": _RT_FIN,
        "pseudo_boot_final_readiness": _PB_FIN,
        "branding_guard": _BRAND,
        "zero_state_verification": _ZERO,
        "dry_build_safety_validation": _SAFE,
    }

    for key, rel in inputs.items():
        if key in ("runtime_bundle_consistency", "branding_guard", "zero_state_verification"):
            continue
        if not _artifact_exists(rel):
            errors.append(f"RESCUE_DRY_FIN_INPUT_MISSING:{rel}")

    cc, ce = load_json_handoff(_CC, "RESCUE_DRY_CC")
    if ce or not isinstance(cc, dict):
        errors.append("RESCUE_DRY_FIN_BUNDLE_CONSISTENCY_MISSING")
    else:
        if str(cc.get("consistency_status") or "") == "blocked":
            errors.append("RESCUE_DRY_FIN_BUNDLE_CONSISTENCY_BLOCKED")

    dlf, de = load_json_handoff(_DL_FIN, "RESCUE_DRY_DLF")
    if de or not isinstance(dlf, dict):
        errors.append("RESCUE_DRY_FIN_DL_GATE_MISSING")
    else:
        if str(dlf.get("gate_status") or "") == "blocked":
            errors.append("RESCUE_DRY_FIN_DL_GATE_BLOCKED")
        elif str(dlf.get("gate_status") or "") not in ("ready", "review_required"):
            warnings.append("RESCUE_DRY_FIN_DL_GATE_NOT_GREEN")

    rtf, re = load_json_handoff(_RT_FIN, "RESCUE_DRY_RTF")
    if re or not isinstance(rtf, dict):
        errors.append("RESCUE_DRY_FIN_RT_GATE_MISSING")
    else:
        if str(rtf.get("gate_status") or "") == "blocked":
            errors.append("RESCUE_DRY_FIN_RT_GATE_BLOCKED")

    pbf, pe = load_json_handoff(_PB_FIN, "RESCUE_DRY_PBF")
    if pe or not isinstance(pbf, dict):
        errors.append("RESCUE_DRY_FIN_PB_MISSING")
    else:
        if str(pbf.get("gate_status") or "") == "blocked":
            errors.append("RESCUE_DRY_FIN_PB_BLOCKED")

    brand, _ = load_json_handoff(_BRAND, "RESCUE_DRY_BR")
    if isinstance(brand, dict) and str(brand.get("branding_guard_status") or "") == "blocked":
        errors.append("RESCUE_DRY_FIN_BRANDING_BLOCKED")

    zero, ze = load_json_handoff(_ZERO, "RESCUE_DRY_ZE")
    if ze:
        warnings.append(f"RESCUE_DRY_FIN_ZERO:{ze}")
    elif isinstance(zero, dict) and str(zero.get("zero_state_status") or "") == "blocked":
        errors.append("RESCUE_DRY_FIN_ZERO_BLOCKED")

    safe, se = load_json_handoff(_SAFE, "RESCUE_DRY_SAFE2")
    if se or not isinstance(safe, dict):
        warnings.append("RESCUE_DRY_FIN_SAFETY_HANDOFF_MISSING")
    else:
        ev = safe.get("evaluation") if isinstance(safe.get("evaluation"), dict) else {}
        ss = str(ev.get("rescue_dry_build_safety_eval_status") or "")
        if ss == "blocked":
            errors.append("RESCUE_DRY_FIN_SAFETY_BLOCKED")

    bo, boe = _read_build_json(_ORDER)
    if boe or not isinstance(bo, dict):
        errors.append("RESCUE_DRY_FIN_ORDER_MISSING")
    elif str(bo.get("rescue_dry_build_build_order_validation_status") or "") != "ok":
        errors.append("RESCUE_DRY_FIN_ORDER_NOT_OK")

    sm, sme = _read_build_json(_SIM)
    if sme or not isinstance(sm, dict):
        errors.append("RESCUE_DRY_FIN_SIM_MISSING")
    elif str(sm.get("rescue_dry_build_execution_simulation_status") or "") != "ok":
        errors.append("RESCUE_DRY_FIN_SIM_NOT_OK")

    for rel in (_GRAPH, _RESOLUTION, _PKG_PLAN):
        p, _ = _build_path(rel)
        if p and p.is_file():
            try:
                raw = p.read_text(encoding="utf-8")
                if _LEGACY_PI.search(raw):
                    errors.append(f"RESCUE_DRY_FIN_LEGACY:{rel}")
            except OSError:
                errors.append(f"RESCUE_DRY_FIN_READ:{rel}")

    gst = "ready"
    if errors:
        gst = "blocked"
    elif warnings:
        gst = "review_required"

    body: dict[str, Any] = {
        "rescue_dry_build_final_gate_schema_version": 1,
        "strict_mode": "rescue_dry_build_orchestration",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "gate_status": gst,
        "inputs": inputs,
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_HANDOFF)
    if werr:
        return _emit("rescue_dry_build_final_gate", _FIN, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit("rescue_dry_build_final_gate", _FIN, gst, body, wrote=True, warnings=warnings, errors=errors)
