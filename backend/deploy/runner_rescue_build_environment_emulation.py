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

_EMUL = "build/rescue/emulation"
_SNAPSHOT = f"{_EMUL}/build_environment_snapshot.json"
_WORKSPACE = f"{_EMUL}/simulated_build_workspace.json"
_OUTPUTS = f"{_EMUL}/simulated_build_outputs.json"
_LOGS = f"{_EMUL}/simulated_build_logs.json"
_OVERLAY = f"{_EMUL}/overlay_persistence_emulation.json"
_SEAL = f"{_EMUL}/build_emulation.seal.json"
_VERIFY = "docs/evidence/runtime-results/handoff/rescue_build_emulation_verify.json"
_FINAL = "docs/evidence/runtime-results/handoff/rescue_build_emulation_final_gate.json"

_MANIFEST = "build/rescue/sandbox_root_manifest.json"
_CFG_RES = "build/rescue/sandbox/manifests/config_copy_result.json"
_RT_RES = "build/rescue/sandbox/manifests/runtime_copy_result.json"
_RT_BUNDLE_SEAL = "build/rescue/runtime_bundle.seal.json"
_OVL = "build/rescue/overlay_workspace_plan.json"
_SB_COPY_FIN = "docs/evidence/runtime-results/handoff/rescue_sandbox_copy_final_gate.json"
_BRAND = "docs/evidence/runtime-results/handoff/setuphelfer_branding_guard_check.json"
_ZERO = "docs/evidence/runtime-results/handoff/runtime_identifier_zero_state_verification.json"

_LEGACY_PI = re.compile(r"(?<![A-Za-z0-9_])pi[-_]installer(?![A-Za-z0-9_])")
_BLOCKED_SUF = (".iso", ".img", ".qcow2", ".qcow", ".vdi", ".vmdk", ".squashfs")

_EXPECTED_EMUL_JSON = frozenset(
    {
        "build_environment_snapshot.json",
        "simulated_build_workspace.json",
        "simulated_build_outputs.json",
        "simulated_build_logs.json",
        "overlay_persistence_emulation.json",
    }
)


def _rx(expr: str) -> re.Pattern[str]:
    return re.compile(expr)


_lb = "lb" + r"\s+build"
_debo = "deb" + "ootstrap"
_ch = "ch" + "ro" + "ot" + r"\s*\("
_mnt = "mount" + r"\s*\("
_grub = "grub-mk" + "rescue"
_xor = "xor" + "riso"

_FORBIDDEN: tuple[tuple[re.Pattern[str], str], ...] = (
    (_rx(r"(?i)" + _lb), "lb_build"),
    (_rx(r"(?i)\b" + _debo + r"\b"), "debootstrap"),
    (_rx(r"(?i)\bapt\s+install\b"), "apt_install"),
    (_rx(r"(?i)" + _ch), "chroot_invoke"),
    (_rx(r"(?i)\bsquashfs\b"), "squashfs_tool"),
    (_rx(r"(?i)\b" + _grub + r"\b"), "grub_mkrescue"),
    (_rx(r"(?i)\b" + _xor + r"\b"), "xorriso"),
    (_rx(r"(?i)" + _mnt), "mount_invoke"),
)


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
    return resolve_under_build_rescue(raw, "RESCUE_BEMUL")


def _write_build_json(path: Path, obj: dict[str, Any]) -> str | None:
    text = json.dumps(obj, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_MANIFEST:
        return "RESCUE_BEMUL_MANIFEST_TOO_LARGE"
    try:
        atomic_write_text(path, text)
    except OSError:
        return "RESCUE_BEMUL_WRITE_FAILED"
    return None


def _file_exists_rel(rel: str) -> bool:
    p, err = _build_path(rel)
    return bool(p and p.is_file() and not err)


def _brief_artifact(rel: str) -> dict[str, Any]:
    p, err = _build_path(rel)
    if err or p is None:
        return {"path": rel, "present": False}
    if not p.is_file():
        return {"path": rel, "present": False}
    try:
        st = p.stat()
        return {"path": rel, "present": True, "size_bytes": st.st_size}
    except OSError:
        return {"path": rel, "present": False, "stat_error": True}


def build_rescue_build_environment_snapshot(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    rp, rerr = _build_path(_SNAPSHOT)
    if rerr or rp is None:
        return _emit("rescue_build_emulation_environment_snapshot", _SNAPSHOT, "blocked", {}, wrote=False, warnings=[], errors=[rerr or "PATH"])
    g = guard_handoff_overwrite(rp, explicit_overwrite=explicit_overwrite, prefix="RESCUE_BEMUL_SN")
    if g:
        return _emit("rescue_build_emulation_environment_snapshot", _SNAPSHOT, "blocked", {}, wrote=False, warnings=[], errors=[g])

    if not _file_exists_rel(_MANIFEST):
        warnings.append("RESCUE_BEMUL_SN_MANIFEST_MISSING")
    if not _file_exists_rel(_OVL):
        warnings.append("RESCUE_BEMUL_SN_OVERLAY_PLAN_MISSING")

    body: dict[str, Any] = {
        "build_environment_snapshot_schema_version": 1,
        "config_copy_state": _brief_artifact(_CFG_RES),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "no_real_build_execution": True,
        "overlay_workspace_state": _brief_artifact(_OVL),
        "readonly_flags": {
            "emulation_only": True,
            "no_binary_iso_write": True,
            "no_live_build_invoke": True,
        },
        "runtime_bundle_state": _brief_artifact(_RT_BUNDLE_SEAL),
        "runtime_copy_state": _brief_artifact(_RT_RES),
        "sandbox_state": _brief_artifact(_MANIFEST),
        "strict_mode": "rescue_build_environment_emulation",
    }
    st = "blocked" if errors else ("review_required" if warnings else "ok")
    werr = _write_build_json(rp, body)
    if werr:
        return _emit("rescue_build_emulation_environment_snapshot", _SNAPSHOT, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit("rescue_build_emulation_environment_snapshot", _SNAPSHOT, st, body, wrote=True, warnings=warnings, errors=errors)


def build_rescue_simulated_build_workspace(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    rp, rerr = _build_path(_WORKSPACE)
    if rerr or rp is None:
        return _emit("rescue_build_emulation_workspace", _WORKSPACE, "blocked", {}, wrote=False, warnings=[], errors=[rerr or "PATH"])
    g = guard_handoff_overwrite(rp, explicit_overwrite=explicit_overwrite, prefix="RESCUE_BEMUL_WS")
    if g:
        return _emit("rescue_build_emulation_workspace", _WORKSPACE, "blocked", {}, wrote=False, warnings=[], errors=[g])

    tree: dict[str, Any] = {
        "build/rescue/debian-live": {"emulated": True, "role": "config_lower_template"},
        "build/rescue/emulation": {"emulated": True, "role": "readonly_emulation_root"},
        "build/rescue/live-build": {"emulated": True, "role": "live_build_stub"},
        "build/rescue/output": {"emulated": True, "role": "simulated_iso_target_dir"},
        "build/rescue/runtime": {"emulated": True, "role": "runtime_staging"},
        "build/rescue/sandbox/config-copy": {"emulated": True, "role": "sandbox_config_mirror"},
        "build/rescue/sandbox/overlay/upper": {"emulated": True, "role": "overlay_upper"},
        "build/rescue/sandbox/overlay/work": {"emulated": True, "role": "overlay_work"},
        "build/rescue/sandbox/runtime-copy": {"emulated": True, "role": "sandbox_runtime_mirror"},
        "build/rescue/sandbox/tmp": {"emulated": True, "role": "temp_dir"},
    }
    body: dict[str, Any] = {
        "emulated_live_build_workdirs": [
            "build/rescue/live-build/cache",
            "build/rescue/live-build/chroot_stub (emulated, not created)",
            "build/rescue/live-build/config",
        ],
        "expected_runtime_placement": "build/rescue/runtime → sandbox/runtime-copy (planned)",
        "filesystem_tree": tree,
        "generated_manifests_emulated": [
            "build/rescue/sandbox_root_manifest.json",
            "build/rescue/sandbox_config_copy_plan.json",
            "build/rescue/sandbox_runtime_copy_plan.json",
        ],
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "readonly_emulated": True,
        "simulated_build_workspace_schema_version": 1,
        "strict_mode": "rescue_build_environment_emulation",
        "temporary_dirs_emulated": ["build/rescue/sandbox/tmp", "build/rescue/sandbox/logs"],
    }
    st = "blocked" if errors else ("review_required" if warnings else "ok")
    werr = _write_build_json(rp, body)
    if werr:
        return _emit("rescue_build_emulation_workspace", _WORKSPACE, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit("rescue_build_emulation_workspace", _WORKSPACE, st, body, wrote=True, warnings=warnings, errors=errors)


def build_rescue_simulated_build_outputs(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    rp, rerr = _build_path(_OUTPUTS)
    if rerr or rp is None:
        return _emit("rescue_build_emulation_outputs", _OUTPUTS, "blocked", {}, wrote=False, warnings=[], errors=[rerr or "PATH"])
    g = guard_handoff_overwrite(rp, explicit_overwrite=explicit_overwrite, prefix="RESCUE_BEMUL_OUT")
    if g:
        return _emit("rescue_build_emulation_outputs", _OUTPUTS, "blocked", {}, wrote=False, warnings=[], errors=[g])

    artifacts: list[dict[str, Any]] = [
        {
            "expected_size_range_bytes": [64 * 1024 * 1024, 900 * 1024 * 1024],
            "filename": "live/filesystem.sqfs",
            "generated": False,
            "readonly_emulated": True,
        },
        {
            "expected_size_range_bytes": [8 * 1024 * 1024, 120 * 1024 * 1024],
            "filename": "live/initrd.img",
            "generated": False,
            "readonly_emulated": True,
        },
        {
            "expected_size_range_bytes": [4 * 1024 * 1024, 20 * 1024 * 1024],
            "filename": "live/vmlinuz",
            "generated": False,
            "readonly_emulated": True,
        },
        {
            "expected_size_range_bytes": [0, 512 * 1024],
            "filename": "EFI/boot/bootx64.efi",
            "generated": False,
            "readonly_emulated": True,
        },
        {
            "expected_size_range_bytes": [0, 64 * 1024],
            "filename": "boot/grub/grub.cfg",
            "generated": False,
            "readonly_emulated": True,
        },
        {
            "expected_size_range_bytes": [0, 32 * 1024],
            "filename": "manifest/sha256sums.txt",
            "generated": False,
            "readonly_emulated": True,
        },
    ]
    body: dict[str, Any] = {
        "boot_catalog_emulated": ["isolinux/boot.cat (emulated)", "efi_boot.img (emulated)"],
        "efi_structure_emulated": ["EFI/BOOT/", "EFI/debian/"],
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "manifest_files_emulated": [a["filename"] for a in artifacts if "manifest" in a["filename"] or "sha256" in a["filename"]],
        "simulated_artifacts": artifacts,
        "simulated_build_outputs_schema_version": 1,
        "strict_mode": "rescue_build_environment_emulation",
    }
    st = "blocked" if errors else ("review_required" if warnings else "ok")
    werr = _write_build_json(rp, body)
    if werr:
        return _emit("rescue_build_emulation_outputs", _OUTPUTS, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit("rescue_build_emulation_outputs", _OUTPUTS, st, body, wrote=True, warnings=warnings, errors=errors)


def build_rescue_simulated_build_logs(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    rp, rerr = _build_path(_LOGS)
    if rerr or rp is None:
        return _emit("rescue_build_emulation_logs", _LOGS, "blocked", {}, wrote=False, warnings=[], errors=[rerr or "PATH"])
    g = guard_handoff_overwrite(rp, explicit_overwrite=explicit_overwrite, prefix="RESCUE_BEMUL_LOG")
    if g:
        return _emit("rescue_build_emulation_logs", _LOGS, "blocked", {}, wrote=False, warnings=[], errors=[g])

    stages: list[dict[str, Any]] = [
        {
            "duration_ms_simulated": 120,
            "expected_readonly_checks": ["sandbox_path_containment", "no_mount_invocation"],
            "expected_validation_messages": ["emulation: skip live-build hook execution"],
            "expected_warnings": ["simulated: cache directory empty"],
            "stage_id": "bootstrap_stub",
        },
        {
            "duration_ms_simulated": 80,
            "expected_readonly_checks": ["hash_manifest_consistency"],
            "expected_validation_messages": ["emulation: runtime bundle seal referenced"],
            "expected_warnings": [],
            "stage_id": "config_resolve",
        },
        {
            "duration_ms_simulated": 200,
            "expected_readonly_checks": ["no_iso_write", "no_compressed_rootfs_pack"],
            "expected_validation_messages": ["emulation: compressed rootfs pack skipped"],
            "expected_warnings": ["simulated: filesystem.sqfs not materialized"],
            "stage_id": "image_pack_stub",
        },
        {
            "duration_ms_simulated": 50,
            "expected_readonly_checks": ["branding_guard_ok", "zero_state_ok"],
            "expected_validation_messages": ["emulation: final readonly gate"],
            "expected_warnings": [],
            "stage_id": "finalize_stub",
        },
    ]
    body: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "no_real_log_capture": True,
        "ordered_stages": stages,
        "simulated_build_logs_schema_version": 1,
        "strict_mode": "rescue_build_environment_emulation",
    }
    st = "blocked" if errors else ("review_required" if warnings else "ok")
    werr = _write_build_json(rp, body)
    if werr:
        return _emit("rescue_build_emulation_logs", _LOGS, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit("rescue_build_emulation_logs", _LOGS, st, body, wrote=True, warnings=warnings, errors=errors)


def build_rescue_overlay_persistence_emulation(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    rp, rerr = _build_path(_OVERLAY)
    if rerr or rp is None:
        return _emit("rescue_build_emulation_overlay", _OVERLAY, "blocked", {}, wrote=False, warnings=[], errors=[rerr or "PATH"])
    g = guard_handoff_overwrite(rp, explicit_overwrite=explicit_overwrite, prefix="RESCUE_BEMUL_OV")
    if g:
        return _emit("rescue_build_emulation_overlay", _OVERLAY, "blocked", {}, wrote=False, warnings=[], errors=[g])

    body: dict[str, Any] = {
        "expected_recovery_behavior": "discard_overlay_upper_on_rollback_emulated",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lowerdir": "build/rescue/runtime",
        "overlay_persistence_emulation_schema_version": 1,
        "persistence_disabled": True,
        "readonly_runtime": True,
        "rollback_behavior": "remove_upper_and_work_dirs_without_mount",
        "strict_mode": "rescue_build_environment_emulation",
        "upperdir": "build/rescue/sandbox/overlay/upper",
        "workdir": "build/rescue/sandbox/overlay/work",
    }
    st = "blocked" if errors else ("review_required" if warnings else "ok")
    werr = _write_build_json(rp, body)
    if werr:
        return _emit("rescue_build_emulation_overlay", _OVERLAY, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit("rescue_build_emulation_overlay", _OVERLAY, st, body, wrote=True, warnings=warnings, errors=errors)


def _scan_forbidden(raw: str) -> list[str]:
    hits: list[str] = []
    for rx, lid in _FORBIDDEN:
        if rx.search(raw):
            hits.append(f"RESCUE_BEMUL_FORBIDDEN:{lid}")
    return hits


def _scan_legacy(raw: str) -> bool:
    return bool(_LEGACY_PI.search(raw))


def verify_rescue_build_emulation(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_VERIFY, "RESCUE_BEMUL_V")
    if oerr or out_path is None:
        return _emit("rescue_build_emulation_verify", _VERIFY, "blocked", {}, wrote=False, warnings=[], errors=[oerr or "INVALID"])
    g0 = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_BEMUL_V")
    if g0:
        return _emit("rescue_build_emulation_verify", _VERIFY, "blocked", {}, wrote=False, warnings=[], errors=[g0])

    warnings: list[str] = []
    errors: list[str] = []

    emul_root, er = _build_path(_EMUL)
    allowed_emul_names = set(_EXPECTED_EMUL_JSON) | {"build_emulation.seal.json"}
    if er or emul_root is None:
        errors.append("RESCUE_BEMUL_V_EMUL_ROOT")
    elif emul_root.is_dir():
        for fp in emul_root.rglob("*"):
            if fp.is_dir():
                continue
            try:
                rel = fp.relative_to(REPO_ROOT).as_posix()
            except ValueError:
                errors.append("RESCUE_BEMUL_V_PATH")
                continue
            name = fp.name
            if not name.lower().endswith(".json"):
                errors.append(f"RESCUE_BEMUL_V_NON_JSON:{rel}")
                continue
            if name not in allowed_emul_names:
                warnings.append(f"RESCUE_BEMUL_V_EXTRA_JSON:{rel}")
            for suf in _BLOCKED_SUF:
                if name.lower().endswith(suf):
                    errors.append(f"RESCUE_BEMUL_V_BLOCKED_SUF:{rel}")
            try:
                sz = fp.stat().st_size
            except OSError:
                errors.append(f"RESCUE_BEMUL_V_STAT:{rel}")
                continue
            if sz > _MAX_MANIFEST:
                errors.append(f"RESCUE_BEMUL_V_LARGE:{rel}")

    for rel in (_SNAPSHOT, _WORKSPACE, _OUTPUTS, _LOGS, _OVERLAY):
        p, pe = _build_path(rel)
        if pe or p is None or not p.is_file():
            errors.append(f"RESCUE_BEMUL_V_MISSING:{rel}")
            continue
        try:
            raw = p.read_text(encoding="utf-8")
        except OSError:
            errors.append(f"RESCUE_BEMUL_V_READ:{rel}")
            continue
        if _scan_legacy(raw):
            errors.append(f"RESCUE_BEMUL_V_LEGACY:{rel}")
        for h in _scan_forbidden(raw):
            errors.append(f"{h}:{rel}")

    out_p, oute = _build_path(_OUTPUTS)
    if not oute and out_p and out_p.is_file():
        try:
            oj = json.loads(out_p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            errors.append("RESCUE_BEMUL_V_OUTPUTS_JSON")
            oj = {}
        arts = oj.get("simulated_artifacts") if isinstance(oj.get("simulated_artifacts"), list) else []
        for a in arts:
            if not isinstance(a, dict):
                errors.append("RESCUE_BEMUL_V_ART_BAD")
                continue
            if a.get("generated") is not False:
                errors.append(f"RESCUE_BEMUL_V_GENERATED:{a.get('filename')}")
            if a.get("readonly_emulated") is not True:
                errors.append(f"RESCUE_BEMUL_V_RO:{a.get('filename')}")

    st = "blocked" if errors else ("review_required" if warnings else "ok")
    body: dict[str, Any] = {
        "build_emulation_verify_schema_version": 1,
        "emulation_files_expected": sorted(_EXPECTED_EMUL_JSON),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "strict_mode": "rescue_build_environment_emulation",
        "verify_eval_status": st,
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_HANDOFF)
    if werr:
        return _emit("rescue_build_emulation_verify", _VERIFY, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit("rescue_build_emulation_verify", _VERIFY, st, body, wrote=True, warnings=warnings, errors=errors)


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def build_rescue_build_emulation_seal(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    sp, serr = _build_path(_SEAL)
    if serr or sp is None:
        return _emit("rescue_build_emulation_seal", _SEAL, "blocked", {}, wrote=False, warnings=[], errors=[serr or "PATH"])
    g = guard_handoff_overwrite(sp, explicit_overwrite=explicit_overwrite, prefix="RESCUE_BEMUL_SEAL")
    if g:
        return _emit("rescue_build_emulation_seal", _SEAL, "blocked", {}, wrote=False, warnings=[], errors=[g])

    vp, ve = resolve_handoff_path(_VERIFY, "RESCUE_BEMUL_V2")
    if ve or vp is None or not vp.is_file():
        return _emit("rescue_build_emulation_seal", _SEAL, "blocked", {}, wrote=False, warnings=[], errors=["RESCUE_BEMUL_SEAL_VERIFY_MISSING"])
    try:
        vo = json.loads(vp.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _emit("rescue_build_emulation_seal", _SEAL, "blocked", {}, wrote=False, warnings=[], errors=["RESCUE_BEMUL_SEAL_VERIFY_JSON"])
    vs = str(vo.get("verify_eval_status") or "")
    if vs == "blocked":
        return _emit("rescue_build_emulation_seal", _SEAL, "blocked", vo, wrote=False, warnings=[], errors=["RESCUE_BEMUL_SEAL_VERIFY_BLOCKED"])
    if vs not in ("ok", "review_required"):
        return _emit("rescue_build_emulation_seal", _SEAL, "blocked", vo, wrote=False, warnings=[], errors=["RESCUE_BEMUL_SEAL_VERIFY_NOT_GREEN"])

    file_hashes: dict[str, str] = {}
    for label, rel in (
        ("build_environment_snapshot_sha256", _SNAPSHOT),
        ("simulated_build_workspace_sha256", _WORKSPACE),
        ("simulated_build_outputs_sha256", _OUTPUTS),
        ("simulated_build_logs_sha256", _LOGS),
        ("overlay_persistence_emulation_sha256", _OVERLAY),
    ):
        p, err = _build_path(rel)
        if err or p is None or not p.is_file():
            errors.append(f"RESCUE_BEMUL_SEAL_MISSING:{rel}")
            continue
        try:
            file_hashes[label] = _sha256_bytes(p.read_bytes())
        except OSError:
            errors.append(f"RESCUE_BEMUL_SEAL_READ:{rel}")

    try:
        file_hashes["build_emulation_verify_handoff_sha256"] = _sha256_bytes(vp.read_bytes())
    except OSError:
        errors.append("RESCUE_BEMUL_SEAL_VERIFY_READ")

    bundle_obj = {"file_hashes": dict(sorted(file_hashes.items())), "schema_version": 1}
    bundle_canonical = json.dumps(bundle_obj, sort_keys=True)
    bundle_sha256 = _sha256_bytes(bundle_canonical.encode("utf-8"))

    seal_st = "blocked" if errors else ("review_required" if warnings else "ok")
    body: dict[str, Any] = {
        "build_emulation_seal_schema_version": 1,
        "bundle_sha256": bundle_sha256,
        "file_hashes": file_hashes,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rescue_build_emulation_seal_status": seal_st,
        "seal_status": seal_st,
        "strict_mode": "rescue_build_environment_emulation",
    }
    if seal_st == "blocked":
        return _emit("rescue_build_emulation_seal", _SEAL, seal_st, body, wrote=False, warnings=warnings, errors=errors)
    werr = _write_build_json(sp, body)
    if werr:
        return _emit("rescue_build_emulation_seal", _SEAL, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit("rescue_build_emulation_seal", _SEAL, seal_st, body, wrote=True, warnings=warnings, errors=errors)


def build_rescue_build_emulation_final_gate(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_FINAL, "RESCUE_BEMUL_FG")
    if oerr or out_path is None:
        return _emit("rescue_build_emulation_final_gate", _FINAL, "blocked", {}, wrote=False, warnings=[], errors=[oerr or "INVALID"])
    g0 = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_BEMUL_FG")
    if g0:
        return _emit("rescue_build_emulation_final_gate", _FINAL, "blocked", {}, wrote=False, warnings=[], errors=[g0])

    warnings: list[str] = []
    errors: list[str] = []

    inputs: dict[str, str] = {
        "branding_guard": _BRAND,
        "build_emulation_seal": _SEAL,
        "build_emulation_verify": _VERIFY,
        "build_environment_snapshot": _SNAPSHOT,
        "overlay_persistence_emulation": _OVERLAY,
        "sandbox_copy_final_gate": _SB_COPY_FIN,
        "simulated_build_logs": _LOGS,
        "simulated_build_outputs": _OUTPUTS,
        "simulated_build_workspace": _WORKSPACE,
        "zero_state_verification": _ZERO,
    }

    for key, rel in inputs.items():
        if key in ("branding_guard", "zero_state_verification"):
            continue
        if key in ("build_emulation_verify", "sandbox_copy_final_gate"):
            p, e = resolve_handoff_path(rel, "RESCUE_BEMUL_FG2")
            if e or p is None or not p.is_file():
                errors.append(f"RESCUE_BEMUL_FG_MISSING:{rel}")
        else:
            p, e = _build_path(rel)
            if e or p is None or not p.is_file():
                errors.append(f"RESCUE_BEMUL_FG_MISSING:{rel}")

    vv, vve = load_json_handoff(_VERIFY, "RESCUE_BEMUL_FG3")
    if vve or not isinstance(vv, dict):
        errors.append("RESCUE_BEMUL_FG_VERIFY_MISSING")
    else:
        vvs = str(vv.get("verify_eval_status") or "")
        if vvs == "blocked":
            errors.append("RESCUE_BEMUL_FG_VERIFY_BLOCKED")
        elif vvs == "review_required":
            warnings.append("RESCUE_BEMUL_FG_VERIFY_REVIEW")

    seal_p, se = _build_path(_SEAL)
    if se or seal_p is None or not seal_p.is_file():
        errors.append("RESCUE_BEMUL_FG_SEAL_MISSING")
    else:
        try:
            so = json.loads(seal_p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            errors.append("RESCUE_BEMUL_FG_SEAL_JSON")
            so = {}
        ss = str(so.get("seal_status") or "")
        if ss == "blocked":
            errors.append("RESCUE_BEMUL_FG_SEAL_BLOCKED")
        elif ss == "review_required":
            warnings.append("RESCUE_BEMUL_FG_SEAL_REVIEW")

    sbc, sbe = load_json_handoff(_SB_COPY_FIN, "RESCUE_BEMUL_SBC")
    if sbe or not isinstance(sbc, dict):
        warnings.append("RESCUE_BEMUL_FG_SANDBOX_COPY_MISSING")
    else:
        gs = str(sbc.get("gate_status") or "")
        if gs == "blocked":
            errors.append("RESCUE_BEMUL_FG_SANDBOX_COPY_BLOCKED")
        elif gs == "review_required":
            warnings.append("RESCUE_BEMUL_FG_SANDBOX_COPY_REVIEW")

    brand, _ = load_json_handoff(_BRAND, "RESCUE_BEMUL_BR")
    if isinstance(brand, dict) and str(brand.get("branding_guard_status") or "") == "blocked":
        errors.append("RESCUE_BEMUL_FG_BRAND")

    zero, ze = load_json_handoff(_ZERO, "RESCUE_BEMUL_ZE")
    if ze:
        warnings.append(f"RESCUE_BEMUL_FG_ZERO:{ze}")
    elif isinstance(zero, dict) and str(zero.get("zero_state_status") or "") == "blocked":
        errors.append("RESCUE_BEMUL_FG_ZERO_BLOCKED")

    emul_root, er = _build_path(_EMUL)
    if not er and emul_root and emul_root.is_dir():
        for fp in emul_root.iterdir():
            if fp.is_file() and fp.suffix.lower() not in (".json",):
                errors.append(f"RESCUE_BEMUL_FG_REAL_ARTIFACT:{fp.name}")

    gst = "ready"
    if errors:
        gst = "blocked"
    elif warnings:
        gst = "review_required"

    body: dict[str, Any] = {
        "gate_status": gst,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "inputs": inputs,
        "rescue_build_emulation_final_gate_schema_version": 1,
        "strict_mode": "rescue_build_environment_emulation",
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_HANDOFF)
    if werr:
        return _emit("rescue_build_emulation_final_gate", _FINAL, "blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit("rescue_build_emulation_final_gate", _FINAL, gst, body, wrote=True, warnings=warnings, errors=errors)
