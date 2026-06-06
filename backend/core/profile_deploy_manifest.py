"""Profile-aware deploy manifests and drift evaluation."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

UTC = timezone.utc

DEVELOPER_CAPABILITY_EXEMPT_API_PREFIXES = frozenset({"/api/dev-dashboard", "/api/dev-server"})


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def profile_manifest_path(profile: str, root: Path | None = None) -> Path:
    base = root or repo_root()
    return base / "deploy" / "manifests" / f"{profile}.manifest.json"


def load_profile_manifest(profile: str, root: Path | None = None) -> dict[str, Any]:
    path = profile_manifest_path(profile, root)
    if not path.is_file():
        return {"profile": profile, "missing": True}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"profile": profile, "invalid": True}
    except json.JSONDecodeError:
        return {"profile": profile, "invalid": True}


def manifest_sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def evaluate_profile_runtime_paths(
    *,
    profile: str,
    runtime_root: Path,
    root: Path | None = None,
) -> dict[str, Any]:
    """Check forbidden paths from profile manifest exist under runtime_root."""
    manifest = load_profile_manifest(profile, root)
    forbidden = manifest.get("forbidden_runtime_paths") or []
    violations: list[str] = []
    for rel in forbidden:
        rel_s = str(rel).replace("\\", "/").lstrip("/")
        if (runtime_root / rel_s).exists():
            violations.append(rel_s)
    status = "green" if not violations else "red"
    return {
        "status": status,
        "forbidden_runtime_present": violations,
        "manifest_profile": profile,
    }


def _path_exists_under(root: Path, rel: str) -> bool:
    rel_s = str(rel).replace("\\", "/").lstrip("/")
    if ".." in rel_s.split("/"):
        return False
    try:
        return (root / rel_s).exists()
    except OSError:
        return False


def _merge_profile_drift_status(*statuses: str) -> str:
    order = {"red": 3, "yellow": 2, "green": 1, "gray": 0}
    best = "green"
    for st in statuses:
        s = str(st or "gray").lower()
        if order.get(s, 0) > order.get(best, 0):
            best = s
    return best


def enrich_deploy_drift_profile_aware(
    base: dict[str, Any],
    *,
    workspace_root: Path,
    runtime_root: Path | None,
    route_paths: list[str] | None = None,
    bind_address: str | None = None,
) -> dict[str, Any]:
    """
    Profile-aware deploy drift slice merged into deploy_drift dict.
    Repo-only dev paths outside profile scope do not affect status.
    """
    from core.install_profile import (
        audit_frontend_backend_profile,
        get_install_profile_state,
        profile_gate_audit_route_paths,
    )

    state = get_install_profile_state()
    profile = state.manifest_profile
    root = repo_root()
    ws_sha = manifest_sha256(profile_manifest_path(profile, root))
    rt_sha: str | None = None
    if runtime_root is not None:
        rt_sha = manifest_sha256(profile_manifest_path(profile, runtime_root))

    manifest = load_profile_manifest(profile, root)
    forbidden_rt = manifest.get("forbidden_runtime_paths") or []
    required_paths = manifest.get("required_paths") or []
    forbidden_api = manifest.get("forbidden_api_paths") or []
    required_api = manifest.get("required_api_paths") or []

    forbidden_present: list[str] = []
    if runtime_root is not None:
        try:
            rt_r = runtime_root.expanduser().resolve()
            for rel in forbidden_rt:
                if _path_exists_under(rt_r, str(rel)):
                    forbidden_present.append(str(rel).replace("\\", "/"))
        except OSError:
            pass

    required_missing: list[str] = []
    if runtime_root is not None:
        try:
            rt_r = runtime_root.expanduser().resolve()
            for rel in required_paths:
                rel_s = str(rel).replace("\\", "/").lstrip("/")
                if not _path_exists_under(rt_r, rel_s):
                    required_missing.append(rel_s)
        except OSError:
            pass

    paths = route_paths or []
    gate_audit = profile_gate_audit_route_paths(paths)
    forbidden_api_visible: list[str] = []
    profile_exposure_forbidden_api: list[str] = []
    developer_capability_exempt_api: list[str] = []
    required_api_missing: list[str] = []

    from core.developer_capability import developer_capability_host_exemption_summary

    cap_host = developer_capability_host_exemption_summary()
    developer_cap_locally_allowed = bool(cap_host.get("locally_allowed_on_host"))

    def _any_api(prefix: str) -> bool:
        return any(p == prefix or p.startswith(prefix + "/") for p in paths)

    for prefix in forbidden_api:
        pfx = str(prefix).rstrip("/")
        if pfx in DEVELOPER_CAPABILITY_EXEMPT_API_PREFIXES and developer_cap_locally_allowed:
            if _any_api(pfx):
                developer_capability_exempt_api.append(pfx)
            continue
        if _any_api(pfx):
            forbidden_api_visible.append(pfx)
            profile_exposure_forbidden_api.append(pfx)
    for prefix in required_api:
        pfx = str(prefix).rstrip("/")
        if not _any_api(pfx):
            required_api_missing.append(pfx)

    profile_manifest_match: bool | None
    if ws_sha and rt_sha:
        profile_manifest_match = ws_sha == rt_sha
    elif ws_sha and not rt_sha:
        profile_manifest_match = None
    else:
        profile_manifest_match = None

    bind = (bind_address or os.environ.get("SETUPHELFER_BIND_ADDRESS") or "127.0.0.1").strip()
    public_status = "green"
    if not state.public_exposure_allowed and bind in ("0.0.0.0", "::", "[::]"):
        if not os.environ.get("SETUPHELFER_OPERATOR_CONFIRM_PUBLIC_BIND"):
            public_status = "red"

    fe_profile = os.environ.get("SETUPHELFER_FRONTEND_BUILD_PROFILE", "").strip()
    fe_audit = audit_frontend_backend_profile(
        frontend_build_profile=fe_profile or None,
        backend_profile=state.install_profile,
    )

    profile_status = "green"
    profile_exposure_status = "green"
    suggested: list[str] = list(base.get("suggested_actions") or [])
    if forbidden_present:
        profile_status = "red"
        profile_exposure_status = "red"
        suggested.append("remove_forbidden_runtime_paths")
    if profile_exposure_forbidden_api or gate_audit.get("profile_gate_errors"):
        profile_status = "red"
        profile_exposure_status = "red"
        suggested.append("disable_dev_api_routes")
    if required_missing:
        profile_status = _merge_profile_drift_status(profile_status, "yellow")
        suggested.append("deploy_required_profile_paths")
    if required_api_missing or gate_audit.get("profile_gate_warnings"):
        profile_status = _merge_profile_drift_status(profile_status, "yellow")
        suggested.append("enable_required_dev_api_routes")
    if public_status == "red":
        profile_status = "red"
        suggested.append("bind_localhost_only")
    if fe_audit.get("frontend_profile_mismatch"):
        profile_status = _merge_profile_drift_status(profile_status, "red")
        suggested.append("rebuild_frontend_profile")

    legacy_status = str(base.get("status") or "gray").lower()
    if profile_status == "green" and profile_manifest_match is True:
        final_status = legacy_status if legacy_status in ("green", "gray") else legacy_status
        if legacy_status == "yellow" and not base.get("missing_runtime_files") and not base.get("differing_files_count"):
            final_status = "green"
    else:
        final_status = _merge_profile_drift_status(legacy_status, profile_status)

    if profile_manifest_match is True and base.get("manifest_match") is False:
        manifest_match_out: bool | None = True
    else:
        manifest_match_out = base.get("manifest_match")

    developer_capability_exposure_status = "allowed" if developer_cap_locally_allowed else "inactive"
    if developer_capability_exempt_api:
        developer_capability_exposure_status = "allowed"

    out = {
        **base,
        "status": final_status,
        "profile_aware": True,
        "install_profile": state.install_profile,
        "manifest_profile": profile,
        "manifest_sha256": ws_sha,
        "workspace_manifest_sha256": ws_sha,
        "runtime_manifest_sha256": rt_sha,
        "profile_manifest_match": profile_manifest_match,
        "manifest_match": manifest_match_out,
        "required_paths_missing": required_missing,
        "forbidden_paths_present": forbidden_present,
        "required_api_paths_missing": required_api_missing,
        "forbidden_api_paths_visible": forbidden_api_visible,
        "profile_exposure": {
            "status": profile_exposure_status,
            "forbidden_api_paths_visible": profile_exposure_forbidden_api,
            "forbidden_paths_present": forbidden_present,
        },
        "developer_capability_exposure": {
            "status": developer_capability_exposure_status,
            "locally_allowed_on_host": developer_cap_locally_allowed,
            "exempt_api_prefixes": developer_capability_exempt_api,
            "dcc_routes_registered": bool(developer_capability_exempt_api),
        },
        "profile_exposure_status": profile_exposure_status,
        "developer_capability_exposure_status": developer_capability_exposure_status,
        "public_exposure_status": public_status,
        "profile_gate_status": gate_audit.get("profile_gate_status"),
        "profile_gate_errors": gate_audit.get("profile_gate_errors", []),
        "profile_gate_warnings": gate_audit.get("profile_gate_warnings", []),
        "frontend_profile_mismatch": fe_audit.get("frontend_profile_mismatch", False),
        "suggested_actions": list(dict.fromkeys(s for s in suggested if s)),
    }
    if not out["suggested_actions"]:
        out["suggested_actions"] = ["none"]
    return out


def build_profile_manifest_data(profile: str, root: Path | None = None) -> dict[str, Any]:
    """Merge common + profile manifest metadata for generator output."""
    base = root or repo_root()
    common = load_profile_manifest("common", base)
    spec = load_profile_manifest(profile, base)
    include = list(dict.fromkeys((common.get("include") or []) + (spec.get("include") or [])))
    exclude = list(dict.fromkeys((common.get("exclude") or []) + (spec.get("exclude") or [])))
    return {
        "manifest_schema_version": 1,
        "profile": profile,
        "generated_at": datetime.now(UTC).isoformat(),
        "include": include,
        "exclude": exclude,
        "required_paths": spec.get("required_paths") or [],
        "forbidden_runtime_paths": spec.get("forbidden_runtime_paths") or [],
        "required_api_paths": spec.get("required_api_paths") or [],
        "forbidden_api_paths": spec.get("forbidden_api_paths") or [],
        "allowed_capabilities": spec.get("allowed_capabilities") or [],
        "forbidden_capabilities": spec.get("forbidden_capabilities") or [],
        "public_exposure_allowed": bool(spec.get("public_exposure_allowed", False)),
    }
