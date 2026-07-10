"""
PI-RS-TEL-003 — Rescue Stick cross-repo telemetry/diagnostics preview verification.

Preview only. No production send. No external calls by default.
"""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urlparse

from core.rescue_lab_telemetry_model import (
    RESCUE_LAB_CREATED_FOR,
    RESCUE_LAB_ENVIRONMENT,
    RESCUE_LAB_PAYLOAD_KIND,
    RESCUE_LAB_PRODUCT,
    RESCUE_LAB_SOURCE,
    validate_rescue_lab_payload_no_pii,
)

PI_RS_TEL_003_CREATED_FOR = "PI-RS-TEL-003"
CSE_TARGET_COMPATIBILITY = "0.1.0-lab2"
DIAGNOSTICS_CONTRACT_REFERENCE = "DIAG-LAB-003"
CLOUDSERVER_PAYLOAD_KIND = "cloudserver_collector_preview"
RESCUE_SOURCE_KIND = "rescue_stick"
RESCUE_EVENT_KIND = "rescue_stick_cross_repo_preview"

ALLOWED_DIAGNOSTICS_HOSTS = frozenset({"127.0.0.1", "localhost"})
_FORBIDDEN_URL_MARKERS = re.compile(
    r"\b(?:Bearer\s+\S+|password\s*=|Authorization:|private[_-]?key)\b",
    re.IGNORECASE,
)


def build_unknown_diagnostics_aggregates() -> dict[str, Any]:
    """Unknown/preview_only aggregates when Rescue Stick has no server inventory."""
    return {
        "plesk": {
            "version_status": "unknown",
            "update_status": "unknown",
            "extension_mode": "preview_only",
        },
        "dns": {
            "status": "unknown",
            "records_status": "unknown",
            "mx_status": "missing",
            "spf_status": "unknown",
        },
        "mail": {
            "service_status": "unknown",
            "tls_status": "unknown",
            "queue_status": "unknown",
        },
        "ssl": {
            "missing_or_unknown_count": 1,
            "expiry_status": "unknown",
            "mode": "preview_only",
            "valid_count": 0,
        },
        "backups": {
            "unknown_count": 1,
            "configured_count": 0,
            "recent_success_status": "missing",
            "restore_test_status": "missing",
            "status": "unknown",
        },
        "restore_verify": {"status": "not_configured"},
        "mail_security": {"status": "unknown", "spf_status": "unknown"},
    }


def build_rescue_cross_repo_telemetry_payload(
    *,
    stick_version: str = "lab-preview-1.9.19.4",
    network_state: str = "unknown",
    gui_available: bool | None = True,
) -> dict[str, Any]:
    """Build PI-RS-TEL-003 rescue telemetry preview payload with cross-repo metadata."""
    return {
        "product": RESCUE_LAB_PRODUCT,
        "source": RESCUE_LAB_SOURCE,
        "source_kind": RESCUE_SOURCE_KIND,
        "event_kind": RESCUE_EVENT_KIND,
        "environment": RESCUE_LAB_ENVIRONMENT,
        "payload_kind": RESCUE_LAB_PAYLOAD_KIND,
        "created_for": PI_RS_TEL_003_CREATED_FOR,
        "created_for_base": RESCUE_LAB_CREATED_FOR,
        "rescue_preview": {
            "stick_version": stick_version,
            "runtime_mode": "rescue_lab_preview",
            "gui_available": gui_available,
            "network_state": network_state,
            "send_flow": "cross_repo_preview_only",
        },
        "diagnostics_aggregates": build_unknown_diagnostics_aggregates(),
        "cross_repo": {
            "cse_target_compatibility": CSE_TARGET_COMPATIBILITY,
            "diagnostics_contract_reference": DIAGNOSTICS_CONTRACT_REFERENCE,
            "preview_only": True,
            "external_calls": False,
            "production_ready": False,
            "auto_apply_enabled": False,
            "operator_approval_required": True,
        },
        "safety": {
            "contains_real_host_data": False,
            "contains_raw_logs": False,
            "contains_secrets": False,
            "contains_mac_addresses": False,
            "contains_ip_addresses": False,
            "production_ready": False,
        },
    }


def build_diagnostics_cloudserver_payload_from_rescue(rescue_payload: dict[str, Any]) -> dict[str, Any]:
    """Map Rescue Stick preview payload to DIAG-LAB-002/003 cloudserver collector preview."""
    aggregates = rescue_payload.get("diagnostics_aggregates")
    if not isinstance(aggregates, dict):
        aggregates = build_unknown_diagnostics_aggregates()

    return {
        "payload_kind": CLOUDSERVER_PAYLOAD_KIND,
        "schema_version": "1.0.0",
        "source_product": "setuphelfer-cloudserver-edition",
        "source_component": "cloudserver-agent",
        "environment": RESCUE_LAB_ENVIRONMENT,
        "production_ready": False,
        "contains_pii": False,
        "contains_secret": False,
        "collector": {
            "collector_mode": "read_only_preview",
            "collector_status": "permission_limited",
            "plesk_write_access": False,
            "customer_data_read": False,
            "domain_names_collected": False,
            "mailbox_addresses_collected": False,
            "database_names_collected": False,
        },
        "aggregates": aggregates,
        "telemetry_connector": {
            "connector_mode": "fixture_preview",
            "cloudserver_lab_client": "unknown",
            "rescue_stick_lab_client": "registered",
            "last_event_summary": "partial",
        },
        "evidence_refs": [
            "evidence:pi_rs_tel_003:rescue_cross_repo_preview",
            f"evidence:stick_version:{rescue_payload.get('rescue_preview', {}).get('stick_version', 'unknown')}",
        ],
        "warnings": ["rescue_stick_preview_only_no_server_inventory"],
        "errors": [],
        "cross_repo_metadata": {
            "source_kind": rescue_payload.get("source_kind", RESCUE_SOURCE_KIND),
            "event_kind": rescue_payload.get("event_kind", RESCUE_EVENT_KIND),
            "cse_target_compatibility": CSE_TARGET_COMPATIBILITY,
            "diagnostics_contract_reference": DIAGNOSTICS_CONTRACT_REFERENCE,
            "preview_only": True,
        },
    }


def validate_cross_repo_preview_contract(payload: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate PI-RS-TEL-003 cross-repo preview contract fields."""
    errors: list[str] = []
    if payload.get("source_kind") != RESCUE_SOURCE_KIND:
        errors.append("source_kind_must_be_rescue_stick")
    if not payload.get("event_kind"):
        errors.append("event_kind_missing")
    cross = payload.get("cross_repo") or {}
    if cross.get("cse_target_compatibility") != CSE_TARGET_COMPATIBILITY:
        errors.append("cse_target_compatibility_mismatch")
    if cross.get("diagnostics_contract_reference") != DIAGNOSTICS_CONTRACT_REFERENCE:
        errors.append("diagnostics_contract_reference_mismatch")
    if bool(cross.get("production_ready")):
        errors.append("production_ready_must_be_false")
    if bool(cross.get("auto_apply_enabled")):
        errors.append("auto_apply_enabled_must_be_false")
    if cross.get("external_calls") is True:
        errors.append("external_calls_must_be_false_default")
    if cross.get("operator_approval_required") is not True:
        errors.append("operator_approval_required")
    if not isinstance(payload.get("diagnostics_aggregates"), dict):
        errors.append("diagnostics_aggregates_missing")

    ok_pii, pii_errors = validate_rescue_lab_payload_no_pii(payload)
    if not ok_pii:
        errors.extend([f"pii:{e}" for e in pii_errors])

    serialized = json.dumps(payload, default=str)
    if _FORBIDDEN_URL_MARKERS.search(serialized):
        errors.append("forbidden_secret_marker")

    return len(errors) == 0, errors


def assert_diagnostics_base_url_allowed(base_url: str) -> None:
    """Reject non-localhost diagnostics endpoints."""
    parsed = urlparse(base_url)
    host = (parsed.hostname or "").lower()
    if host not in ALLOWED_DIAGNOSTICS_HOSTS:
        raise ValueError(f"diagnostics_endpoint_not_allowed:{host}")


def post_diagnostics_json(
    *,
    base_url: str,
    path: str,
    payload: dict[str, Any],
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """POST JSON to local diagnostics server preview API (no Authorization header)."""
    import urllib.error
    import urllib.request

    assert_diagnostics_base_url_allowed(base_url)
    url = f"{base_url.rstrip('/')}{path}"
    body = json.dumps({"payload": payload}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"diagnostics_http_error:{exc.code}:{detail}") from exc


def verify_diagnostics_validate_preview(*, base_url: str, cloudserver_payload: dict[str, Any]) -> dict[str, Any]:
    result = post_diagnostics_json(
        base_url=base_url,
        path="/api/diagnostics/cloudserver/validate",
        payload=cloudserver_payload,
    )
    if result.get("production_ready"):
        raise ValueError("validate_response_not_preview_safe")
    return result


def verify_diagnostics_findings_preview(*, base_url: str, cloudserver_payload: dict[str, Any]) -> dict[str, Any]:
    result = post_diagnostics_json(
        base_url=base_url,
        path="/api/diagnostics/cloudserver/findings-preview",
        payload=cloudserver_payload,
    )
    if result.get("production_ready"):
        raise ValueError("findings_preview_not_preview_safe")
    return result
