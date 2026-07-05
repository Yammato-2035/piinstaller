"""
PI-RS-TEL-002 — profile-aware runtime gate evaluation (release vs lab).
"""

from __future__ import annotations

from typing import Any

RELEASE_PROFILES = frozenset({"release", "production"})
LAB_PROFILES = frozenset({"developer", "local_lab", "rescue_lab"})
VALID_EXPECTED = RELEASE_PROFILES | LAB_PROFILES


def _lab_feature_disabled(http_status: int, body: dict[str, Any] | None) -> bool:
    if http_status == 403:
        return True
    if http_status == 200 and isinstance(body, dict):
        if body.get("feature_enabled") is False:
            return True
        if body.get("reason") == "feature_disabled":
            return True
        errors = body.get("errors") or []
        if any("feature_disabled" in str(e) for e in errors):
            return True
    return False


def _lab_status_loadable(http_status: int, body: dict[str, Any] | None) -> bool:
    if http_status != 200:
        return False
    if not isinstance(body, dict):
        return False
    if body.get("feature_enabled") is False:
        return False
    return bool(body.get("client_id") or body.get("title"))


def evaluate_profile_aware_runtime_gate(
    *,
    expected_profile: str,
    version_http_status: int,
    version_payload: dict[str, Any] | None,
    lab_status_http: int,
    lab_status_body: dict[str, Any] | None,
    dcc_status_http: int,
    service_active: bool,
    backend_runtime_path: str | None = None,
) -> dict[str, Any]:
    profile = (expected_profile or "release").strip().lower()
    warnings: list[str] = []
    errors: list[str] = []

    if profile not in VALID_EXPECTED:
        errors.append(f"invalid_expected_profile:{profile}")
        profile = "release"

    if not service_active:
        errors.append("backend_service_not_active")

    if version_http_status != 200:
        errors.append(f"version_http_status:{version_http_status}")
    elif not isinstance(version_payload, dict) or not version_payload.get("project_version"):
        errors.append("project_version_missing")

    runtime_path = (backend_runtime_path or (version_payload or {}).get("backend_runtime_path") or "").strip()
    if version_http_status == 200 and runtime_path and "/opt/" not in runtime_path and profile in RELEASE_PROFILES:
        warnings.append("backend_runtime_path_not_opt")

    is_release = profile in RELEASE_PROFILES
    is_lab = profile in LAB_PROFILES

    if is_release:
        if not _lab_feature_disabled(lab_status_http, lab_status_body):
            if lab_status_http == 404:
                warnings.append("lab_status_404_runtime_may_lack_pi_rs_tel_deploy")
            else:
                errors.append("release_requires_lab_endpoints_disabled")
        if dcc_status_http == 404:
            pass  # expected in release — not a review warning
        elif dcc_status_http != 200:
            warnings.append(f"dcc_status_http:{dcc_status_http}")

    if is_lab:
        if _lab_feature_disabled(lab_status_http, lab_status_body):
            errors.append("lab_profile_requires_lab_endpoints_enabled")
        elif not _lab_status_loadable(lab_status_http, lab_status_body):
            if lab_status_http == 404:
                errors.append("lab_endpoints_not_registered_deploy_required")
            else:
                errors.append("lab_client_status_not_loadable")

    if errors:
        status = f"{'release' if is_release else 'lab'}_runtime_blocked"
    elif warnings:
        status = f"{'release' if is_release else 'lab'}_runtime_review_required"
    else:
        status = f"{'release' if is_release else 'lab'}_runtime_ok"

    return {
        "profile": profile,
        "status": status,
        "service_active": service_active,
        "version_http_status": version_http_status,
        "project_version": (version_payload or {}).get("project_version"),
        "backend_runtime_path": runtime_path or None,
        "lab_status_http": lab_status_http,
        "lab_endpoints_disabled": _lab_feature_disabled(lab_status_http, lab_status_body),
        "dcc_status_http": dcc_status_http,
        "warnings": warnings,
        "errors": errors,
    }
