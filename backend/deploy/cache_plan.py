from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

_CACHE_CANDIDATES = [
    "/mnt/setuphelfer/cache/deploy",
    "/var/cache/setuphelfer/deploy",
    "./cache/deploy",
]


def _is_internal_host(host: str) -> bool:
    h = (host or "").lower().strip()
    return h in {"localhost", "127.0.0.1", "::1"} or h.endswith(".local") or h.endswith(".internal")


def _source_type(source: dict[str, Any]) -> str:
    t = str(source.get("type") or "")
    if t in {"local_image", "remote_image", "official_installer"}:
        return t
    return ""


def _verification_plan(source: dict[str, Any]) -> dict[str, Any]:
    checksum = str(source.get("checksum") or "")
    checksum_required = bool(source.get("checksum_required")) or str(source.get("type") or "") == "remote_image"
    return {
        "checksum_required": checksum_required,
        "checksum_algorithm": "sha256",
        "expected_checksum": checksum,
        "verify_before_use": True,
        "reject_without_checksum": True,
    }


def _required_steps(source_type: str) -> list[dict[str, Any]]:
    steps = [
        ("DEPLOY_CACHE_STEP_VALIDATE_SOURCE", False, False, True),
        ("DEPLOY_CACHE_STEP_SELECT_CACHE_PATH", False, False, True),
        ("DEPLOY_CACHE_STEP_DOWNLOAD_IMAGE", source_type == "remote_image", source_type == "remote_image", source_type == "remote_image"),
        ("DEPLOY_CACHE_STEP_VERIFY_CHECKSUM", False, False, True),
        ("DEPLOY_CACHE_STEP_MARK_READY_FOR_DEPLOY", False, False, True),
    ]
    out: list[dict[str, Any]] = []
    for code, would_network, would_write, applicable in steps:
        out.append(
            {
                "code": code,
                "applicable": applicable,
                "would_network": bool(would_network),
                "would_write_cache": bool(would_write),
                "requires_confirmation": True,
                "auto_allowed": False,
            }
        )
    return out


def generate_deploy_cache_plan(
    source: dict,
    deploy_plan: dict,
    inspect_result: dict | None = None,
) -> dict:
    src = source if isinstance(source, dict) else {}
    dplan = deploy_plan if isinstance(deploy_plan, dict) else {}
    inspect = inspect_result if isinstance(inspect_result, dict) else {}

    blocked_steps: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []
    risks: list[str] = []

    st = str(dplan.get("plan_status") or "")
    if st not in {"ok", "review_required", "blocked", "not_applicable"}:
        st = "not_applicable"

    source_type = _source_type(src)
    if not source_type:
        blocked_steps.append("DEPLOY_CACHE_BLOCKED_INVALID_SOURCE")
        errors.append("DEPLOY_CACHE_BLOCKED_INVALID_SOURCE")

    if st in {"blocked", "not_applicable"}:
        blocked_steps.append("DEPLOY_CACHE_BLOCKED_INVALID_SOURCE")

    # Keep existing deploy blockers as safety constraints.
    existing_blocked = dplan.get("blocked_steps")
    if isinstance(existing_blocked, list) and existing_blocked:
        blocked_steps.append("DEPLOY_CACHE_BLOCKED_INVALID_SOURCE")

    verification = _verification_plan(src)
    if verification["checksum_required"] and not verification["expected_checksum"]:
        blocked_steps.append("DEPLOY_CACHE_BLOCKED_MISSING_CHECKSUM")

    if source_type == "remote_image":
        url = str(src.get("remote_url") or src.get("url") or "")
        parsed = urlparse(url)
        host = parsed.hostname or ""
        if parsed.scheme != "https":
            blocked_steps.append("DEPLOY_CACHE_BLOCKED_INSECURE_URL")
        if not host or _is_internal_host(host):
            blocked_steps.append("DEPLOY_CACHE_BLOCKED_INTERNAL_URL")
        warnings.append("DEPLOY_CACHE_BLOCKED_NETWORK_FORBIDDEN")
        risks.extend(["DEPLOY_CACHE_RISK_NETWORK_FAILURE", "DEPLOY_CACHE_RISK_UNTRUSTED_SOURCE"])

    if source_type == "local_image":
        # local image only planning, no download needed
        risks.append("DEPLOY_CACHE_RISK_WRONG_ARCHITECTURE")

    if source_type == "official_installer":
        warnings.append("DEPLOY_CACHE_OFFICIAL_INSTALLER_METADATA_ONLY")
        risks.append("DEPLOY_CACHE_RISK_UNTRUSTED_SOURCE")

    # Architecture hint from inspect for defensive risk tag.
    machine = str((inspect.get("system") or {}).get("machine") or (inspect.get("system") or {}).get("architecture") or "")
    if machine and str(src.get("architecture") or "unknown") not in {"unknown", machine, "x86_64" if machine == "amd64" else machine}:
        risks.append("DEPLOY_CACHE_RISK_WRONG_ARCHITECTURE")

    cache_candidates = list(_CACHE_CANDIDATES)
    if not cache_candidates:
        blocked_steps.append("DEPLOY_CACHE_BLOCKED_NO_CACHE_TARGET")

    blocked_steps = list(dict.fromkeys(blocked_steps))
    warnings = list(dict.fromkeys(warnings))
    risks = list(dict.fromkeys(risks + ["DEPLOY_CACHE_RISK_TAMPERED_IMAGE", "DEPLOY_CACHE_RISK_INSUFFICIENT_SPACE"]))

    if blocked_steps:
        plan_status = "blocked"
    elif source_type == "remote_image":
        plan_status = "review_required"
    elif source_type == "local_image":
        plan_status = "ok"
    elif source_type == "official_installer":
        plan_status = "review_required"
    else:
        plan_status = "not_applicable"

    return {
        "plan_status": plan_status,
        "source": {
            "source_id": src.get("source_id"),
            "type": source_type or "unknown",
            "name": src.get("name"),
            "architecture": src.get("architecture", "unknown"),
            "status": src.get("status", "metadata_only"),
        },
        "cache": {
            "cache_targets": cache_candidates,
            "selected_cache_target": None,
            "network_forbidden_now": True,
            "download_executed": False,
            "cache_write_executed": False,
        },
        "verification": verification,
        "required_steps": _required_steps(source_type),
        "blocked_steps": blocked_steps,
        "risks": risks,
        "warnings": warnings,
        "errors": errors,
        "requires_manual_review": plan_status != "ok",
    }
