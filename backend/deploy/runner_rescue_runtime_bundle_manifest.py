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
    guard_handoff_overwrite,
    load_json_handoff,
    resolve_handoff_path,
    resolve_under_build_rescue,
    write_json_handoff,
)

_MAX_MANIFEST = 900_000
_MAX_HANDOFF = 512 * 1024
_MAX_HASH_FILES = 4000

_RUNTIME_ROOT = "build/rescue/runtime"
_INVENTORY_JSON = "build/rescue/runtime_bundle_inventory.json"
_HASH_JSON = "build/rescue/runtime_bundle_hash_manifest.json"
_SEAL_JSON = "build/rescue/runtime_bundle.seal.json"

_HANDOFF_CONSISTENCY = "docs/evidence/runtime-results/handoff/rescue_runtime_bundle_consistency_check.json"
_HANDOFF_ASSEMBLY_FINAL = "docs/evidence/runtime-results/handoff/rescue_runtime_assembly_final_gate.json"
_HANDOFF_ASSEMBLY_SAFETY = "docs/evidence/runtime-results/handoff/rescue_runtime_assembly_safety.json"

_LEGACY_PI = re.compile(r"(?<![A-Za-z0-9_])pi[-_]installer(?![A-Za-z0-9_])")

_EXPECTED_DIRS = (
    "opt/setuphelfer",
    "etc/setuphelfer",
    "var/log/setuphelfer",
    "run/setuphelfer",
    "run/setuphelfer/evidence",
    "run/setuphelfer/recovery",
    "usr/share/setuphelfer/frontend",
    "boot",
    "EFI",
    "live",
    "scripts",
)

_EXPECTED_MANIFESTS = (
    "runtime_root_manifest.json",
    "backend_runtime_assembly.json",
    "frontend_runtime_assembly.json",
    "recovery_runtime_assembly.json",
    "offline_configuration_assembly.json",
    "startup_script_assembly.json",
)

_EXPECTED_SCRIPTS = (
    "scripts/start-backend.sh",
    "scripts/start-frontend.sh",
    "scripts/start-recovery-ui.sh",
    "scripts/shutdown-safe.sh",
)

_BUNDLE_VERSION = "1"


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
    return resolve_under_build_rescue(raw, "RESCUE_BUNDLE")


def _ensure_under_build_rescue(p: Path) -> tuple[bool, str | None]:
    try:
        p.resolve(strict=False).relative_to(BUILD_RESCUE_ROOT.resolve(strict=False))
    except (OSError, ValueError):
        return False, "RESCUE_BUNDLE_OUTSIDE_BUILD_RESCUE"
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
        return "RESCUE_BUNDLE_MANIFEST_TOO_LARGE"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return None


def _canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _runtime_base_path() -> Path | None:
    p, err = _build_path(_RUNTIME_ROOT)
    return p if not err and p is not None else None


def _is_expected_runtime_rel(rel_posix: str) -> bool:
    rp = rel_posix.replace("\\", "/")
    if rp in _EXPECTED_MANIFESTS or rp in _EXPECTED_SCRIPTS:
        return True
    for d in _EXPECTED_DIRS:
        if rp == d or rp.startswith(d + "/"):
            return True
    if rp.endswith("/" + ".setuphelfer_runtime_assembly_placeholder".split("/")[-1]):
        return True
    if "/.setuphelfer_runtime_assembly_placeholder" in rp or rp.endswith(".setuphelfer_runtime_assembly_placeholder"):
        return True
    return False


def build_rescue_runtime_bundle_inventory(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    out_path, oerr = _build_path(_INVENTORY_JSON)
    if oerr or out_path is None:
        return _emit("rescue_runtime_bundle_inventory", _INVENTORY_JSON, "blocked", {}, wrote=False, warnings=[], errors=[oerr or "PATH"])

    g = _guard_build_file(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_BUNDLE_INV")
    if g:
        return _emit("rescue_runtime_bundle_inventory", _INVENTORY_JSON, "blocked", {}, wrote=False, warnings=[], errors=[g])

    rt = _runtime_base_path()
    if rt is None or not rt.is_dir():
        errors.append("RESCUE_BUNDLE_RUNTIME_ROOT_MISSING")

    files: list[str] = []
    dirs: list[str] = []
    legacy_findings: list[str] = []
    unexpected_paths: list[str] = []

    if rt and rt.is_dir():
        for fp in sorted(rt.rglob("*")):
            try:
                rel = fp.relative_to(rt).as_posix()
            except ValueError:
                continue
            if fp.is_symlink():
                try:
                    fp.resolve().relative_to(BUILD_RESCUE_ROOT.resolve(strict=False))
                except (OSError, ValueError):
                    errors.append(f"RESCUE_BUNDLE_SYMLINK_ESCAPE:{rel}")
                    continue
            if fp.is_dir():
                dirs.append(rel)
                continue
            if not fp.is_file():
                continue
            low = fp.name.lower()
            if low.endswith(".iso") or low.endswith(".img"):
                errors.append(f"RESCUE_BUNDLE_FORBIDDEN_IMAGE:{rel}")
                continue
            files.append(rel)
            if not _is_expected_runtime_rel(rel):
                unexpected_paths.append(rel)
            if low.endswith((".json", ".sh")):
                try:
                    raw = fp.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                if _LEGACY_PI.search(raw):
                    legacy_findings.append(rel)

    missing: list[str] = []
    if rt and rt.is_dir():
        for d in _EXPECTED_DIRS:
            if not (rt / d).is_dir():
                missing.append(d)
        for m in _EXPECTED_MANIFESTS:
            if not (rt / m).is_file():
                missing.append(m)
        for sc in _EXPECTED_SCRIPTS:
            if not (rt / sc).is_file():
                missing.append(sc)

    if missing:
        errors.append(f"RESCUE_BUNDLE_MISSING_EXPECTED:{','.join(missing[:20])}")
    if legacy_findings:
        errors.append("RESCUE_BUNDLE_LEGACY_IN_RUNTIME_ARTIFACTS")
    if unexpected_paths and not errors:
        warnings.append(f"RESCUE_BUNDLE_UNEXPECTED_PATHS:{len(unexpected_paths)}")

    inv_st = "ok"
    if errors:
        inv_st = "blocked"
    elif warnings or unexpected_paths:
        inv_st = "review_required"

    body: dict[str, Any] = {
        "runtime_bundle_inventory_schema_version": 1,
        "strict_mode": "rescue_runtime_bundle_manifest",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "root": _RUNTIME_ROOT,
        "files": files,
        "dirs": sorted(set(dirs)),
        "missing_expected_paths": missing,
        "unexpected_paths": sorted(set(unexpected_paths))[:200],
        "legacy_findings": legacy_findings,
        "inventory_status": inv_st,
    }
    werr = _write_json_build(out_path, body)
    if werr:
        return _emit("rescue_runtime_bundle_inventory", _INVENTORY_JSON, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit("rescue_runtime_bundle_inventory", _INVENTORY_JSON, inv_st, body, wrote=True, warnings=warnings, errors=errors)


def build_rescue_runtime_bundle_hash_manifest(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    out_path, oerr = _build_path(_HASH_JSON)
    if oerr or out_path is None:
        return _emit("rescue_runtime_bundle_hash_manifest", _HASH_JSON, "blocked", {}, wrote=False, warnings=[], errors=[oerr or "PATH"])
    g = _guard_build_file(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_BUNDLE_HASH")
    if g:
        return _emit("rescue_runtime_bundle_hash_manifest", _HASH_JSON, "blocked", {}, wrote=False, warnings=[], errors=[g])

    rt = _runtime_base_path()
    if rt is None or not rt.is_dir():
        errors.append("RESCUE_BUNDLE_HASH_RUNTIME_ROOT_MISSING")

    sha_map: dict[str, str] = {}
    sizes: dict[str, int] = {}
    total = 0
    nfiles = 0

    if rt and rt.is_dir():
        for fp in sorted(rt.rglob("*")):
            if not fp.is_file():
                continue
            try:
                rel = fp.relative_to(rt).as_posix()
            except ValueError:
                errors.append("RESCUE_BUNDLE_HASH_PATH_OUTSIDE_RUNTIME")
                continue
            if fp.is_symlink():
                errors.append(f"RESCUE_BUNDLE_HASH_SYMLINK_FILE:{rel}")
                continue
            low = fp.name.lower()
            if low.endswith(".iso") or low.endswith(".img"):
                errors.append(f"RESCUE_BUNDLE_HASH_FORBIDDEN_IMAGE:{rel}")
                continue
            try:
                ok, _ = _ensure_under_build_rescue(fp)
                if not ok:
                    errors.append(f"RESCUE_BUNDLE_HASH_OUTSIDE:{rel}")
                    continue
            except OSError:
                errors.append(f"RESCUE_BUNDLE_HASH_ACCESS:{rel}")
                continue
            if nfiles >= _MAX_HASH_FILES:
                warnings.append("RESCUE_BUNDLE_HASH_FILE_CAP")
                break
            try:
                b = fp.read_bytes()
            except OSError as e:
                errors.append(f"RESCUE_BUNDLE_HASH_READ_FAIL:{rel}:{e!s}")
                continue
            sha_map[rel] = hashlib.sha256(b).hexdigest()
            sizes[rel] = len(b)
            total += len(b)
            nfiles += 1

    hm_st = "ok"
    if errors:
        hm_st = "blocked"
    elif warnings:
        hm_st = "review_required"

    body: dict[str, Any] = {
        "hash_manifest_schema_version": 1,
        "strict_mode": "rescue_runtime_bundle_manifest",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "root": _RUNTIME_ROOT,
        "file_count": nfiles,
        "total_bytes": total,
        "sizes": sizes,
        "sha256": sha_map,
        "hash_manifest_status": hm_st,
    }
    werr = _write_json_build(out_path, body)
    if werr:
        return _emit("rescue_runtime_bundle_hash_manifest", _HASH_JSON, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit("rescue_runtime_bundle_hash_manifest", _HASH_JSON, hm_st, body, wrote=True, warnings=warnings, errors=errors)


def build_rescue_runtime_bundle_seal(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    inv_path, ierr = _build_path(_INVENTORY_JSON)
    hash_path, herr = _build_path(_HASH_JSON)
    seal_path, serr = _build_path(_SEAL_JSON)
    if ierr or inv_path is None or herr or hash_path is None or serr or seal_path is None:
        return _emit("rescue_runtime_bundle_seal", _SEAL_JSON, "blocked", {}, wrote=False, warnings=[], errors=[ierr or herr or serr or "PATH"])

    g = _guard_build_file(seal_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_BUNDLE_SEAL")
    if g:
        return _emit("rescue_runtime_bundle_seal", _SEAL_JSON, "blocked", {}, wrote=False, warnings=[], errors=[g])

    if not inv_path.is_file() or not hash_path.is_file():
        return _emit("rescue_runtime_bundle_seal", _SEAL_JSON, "blocked", {}, wrote=False, warnings=[], errors=["RESCUE_BUNDLE_SEAL_PREREQ_MISSING"])

    inv_raw = inv_path.read_bytes()
    hash_raw = hash_path.read_bytes()
    try:
        inv_obj = json.loads(inv_raw.decode("utf-8"))
        hash_obj = json.loads(hash_raw.decode("utf-8"))
    except json.JSONDecodeError:
        return _emit("rescue_runtime_bundle_seal", _SEAL_JSON, "blocked", {}, wrote=False, warnings=[], errors=["RESCUE_BUNDLE_SEAL_JSON_INVALID"])

    inv_st = str(inv_obj.get("inventory_status") or "")
    hm_st = str(hash_obj.get("hash_manifest_status") or "")
    if inv_st == "blocked" or hm_st == "blocked":
        errors.append("RESCUE_BUNDLE_SEAL_PREREQ_BLOCKED")
    elif inv_st not in ("ok", "review_required") or hm_st not in ("ok", "review_required"):
        errors.append("RESCUE_BUNDLE_SEAL_PREREQ_NOT_OK")

    inventory_sha256 = _sha256_bytes(inv_raw)
    hash_manifest_sha256 = _sha256_bytes(hash_raw)
    bundle_sha256 = _sha256_bytes(_canonical_json_bytes({k: hash_obj[k] for k in sorted(hash_obj.keys())}))

    seal_st = "ok"
    if errors:
        seal_st = "blocked"
    elif warnings or inv_st == "review_required" or hm_st == "review_required":
        seal_st = "review_required"

    body: dict[str, Any] = {
        "runtime_bundle_seal_schema_version": 1,
        "strict_mode": "rescue_runtime_bundle_manifest",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "bundle_version": _BUNDLE_VERSION,
        "inventory_sha256": inventory_sha256,
        "hash_manifest_sha256": hash_manifest_sha256,
        "bundle_sha256": bundle_sha256,
        "seal_status": seal_st,
        "inputs": {"inventory": _INVENTORY_JSON, "hash_manifest": _HASH_JSON},
    }
    if errors:
        return _emit("rescue_runtime_bundle_seal", _SEAL_JSON, seal_st, body, wrote=False, warnings=warnings, errors=errors)
    werr = _write_json_build(seal_path, body)
    if werr:
        return _emit("rescue_runtime_bundle_seal", _SEAL_JSON, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit("rescue_runtime_bundle_seal", _SEAL_JSON, seal_st, body, wrote=True, warnings=warnings, errors=errors)


def check_rescue_runtime_bundle_consistency(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_HANDOFF_CONSISTENCY, "RESCUE_BUNDLE_CC")
    if oerr or out_path is None:
        return _emit("rescue_runtime_bundle_consistency_check", _HANDOFF_CONSISTENCY, "blocked", {}, wrote=False, warnings=[], errors=[oerr or "INVALID"])
    g0 = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_BUNDLE_CC")
    if g0:
        return _emit("rescue_runtime_bundle_consistency_check", _HANDOFF_CONSISTENCY, "blocked", {}, wrote=False, warnings=[], errors=[g0])

    warnings: list[str] = []
    errors: list[str] = []

    inv_path, _ = _build_path(_INVENTORY_JSON)
    hash_path, _ = _build_path(_HASH_JSON)
    seal_path, _ = _build_path(_SEAL_JSON)
    if inv_path is None or hash_path is None or seal_path is None:
        return _emit("rescue_runtime_bundle_consistency_check", _HANDOFF_CONSISTENCY, "blocked", {}, wrote=False, warnings=[], errors=["RESCUE_BUNDLE_CC_PATH"])

    if not inv_path.is_file():
        errors.append("RESCUE_BUNDLE_CC_INVENTORY_MISSING")
    if not hash_path.is_file():
        errors.append("RESCUE_BUNDLE_CC_HASH_MISSING")
    if not seal_path.is_file():
        errors.append("RESCUE_BUNDLE_CC_SEAL_MISSING")

    seal_obj: dict[str, Any] = {}
    inv_obj: dict[str, Any] = {}
    hash_obj: dict[str, Any] = {}
    if inv_path.is_file() and hash_path.is_file() and seal_path.is_file():
        try:
            inv_obj = json.loads(inv_path.read_text(encoding="utf-8"))
            hash_obj = json.loads(hash_path.read_text(encoding="utf-8"))
            seal_obj = json.loads(seal_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            errors.append("RESCUE_BUNDLE_CC_JSON_INVALID")

    inv_raw = inv_path.read_bytes() if inv_path.is_file() else b""
    hash_raw = hash_path.read_bytes() if hash_path.is_file() else b""
    if seal_obj:
        if seal_obj.get("inventory_sha256") != _sha256_bytes(inv_raw):
            errors.append("RESCUE_BUNDLE_CC_INVENTORY_HASH_MISMATCH")
        if seal_obj.get("hash_manifest_sha256") != _sha256_bytes(hash_raw):
            errors.append("RESCUE_BUNDLE_CC_HASH_MANIFEST_HASH_MISMATCH")
        expected_bundle = _sha256_bytes(_canonical_json_bytes({k: hash_obj[k] for k in sorted(hash_obj.keys())}))
        if seal_obj.get("bundle_sha256") != expected_bundle:
            errors.append("RESCUE_BUNDLE_CC_BUNDLE_HASH_MISMATCH")

    rt = _runtime_base_path()
    sha_expected = hash_obj.get("sha256") if isinstance(hash_obj.get("sha256"), dict) else {}
    if isinstance(sha_expected, dict) and rt and rt.is_dir():
        for rel, expected_hex in sha_expected.items():
            fp = rt / Path(rel)
            if not fp.is_file():
                errors.append(f"RESCUE_BUNDLE_CC_FILE_MISSING:{rel}")
                continue
            if _sha256_file(fp) != str(expected_hex):
                errors.append(f"RESCUE_BUNDLE_CC_CONTENT_HASH_MISMATCH:{rel}")

    miss = inv_obj.get("missing_expected_paths") if isinstance(inv_obj.get("missing_expected_paths"), list) else []
    if miss:
        errors.append("RESCUE_BUNDLE_CC_MISSING_PATHS_IN_INVENTORY")

    leg = inv_obj.get("legacy_findings") if isinstance(inv_obj.get("legacy_findings"), list) else []
    if leg:
        errors.append("RESCUE_BUNDLE_CC_LEGACY_ACTIVE")

    if inv_obj.get("inventory_status") == "blocked":
        errors.append("RESCUE_BUNDLE_CC_INVENTORY_BLOCKED")

    fin, _ = load_json_handoff(_HANDOFF_ASSEMBLY_FINAL, "RB_FIN")
    if not isinstance(fin, dict):
        errors.append("RESCUE_BUNDLE_CC_ASSEMBLY_FINAL_MISSING")
    else:
        gs = str(fin.get("gate_status") or "")
        if gs == "blocked":
            errors.append("RESCUE_BUNDLE_CC_ASSEMBLY_FINAL_BLOCKED")
        elif gs not in ("ready", "review_required"):
            warnings.append("RESCUE_BUNDLE_CC_ASSEMBLY_FINAL_NOT_READY")

    safe, _ = load_json_handoff(_HANDOFF_ASSEMBLY_SAFETY, "RB_SAFE")
    if isinstance(safe, dict):
        ev = safe.get("evaluation") if isinstance(safe.get("evaluation"), dict) else {}
        st = str(ev.get("rescue_runtime_assembly_safety_eval_status") or "")
        if st == "blocked":
            errors.append("RESCUE_BUNDLE_CC_SAFETY_BLOCKED")
        elif st not in ("ok", "review_required"):
            warnings.append("RESCUE_BUNDLE_CC_SAFETY_NOT_OK_OR_REVIEW")
    else:
        warnings.append("RESCUE_BUNDLE_CC_SAFETY_HANDOFF_MISSING")

    fc = int(hash_obj.get("file_count") or 0)
    if fc < 4 and not errors:
        warnings.append("RESCUE_BUNDLE_CC_FILE_COUNT_LOW")

    cc_st = "ok"
    if errors:
        cc_st = "blocked"
    elif warnings:
        cc_st = "review_required"

    body: dict[str, Any] = {
        "rescue_runtime_bundle_consistency_schema_version": 1,
        "strict_mode": "rescue_runtime_bundle_manifest",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "consistency_status": cc_st,
        "inventory_path": _INVENTORY_JSON,
        "hash_manifest_path": _HASH_JSON,
        "seal_path": _SEAL_JSON,
        "file_count_observed": fc,
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_HANDOFF)
    if werr:
        return _emit("rescue_runtime_bundle_consistency_check", _HANDOFF_CONSISTENCY, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit("rescue_runtime_bundle_consistency_check", _HANDOFF_CONSISTENCY, cc_st, body, wrote=True, warnings=warnings, errors=errors)
