"""Ingest-Logik für Development-Server-Berichte."""

from __future__ import annotations

from typing import Any

from devserver.config import DevServerConfig
from devserver.models import default_dev_node, default_dev_report, merge_node_update, new_id, utc_now_iso
from devserver.redaction import apply_lab_mode_redaction, detect_forbidden_sensitive_fields
from devserver.storage import DevServerStorage


def _validate_token(config: DevServerConfig, token: str | None) -> tuple[bool, list[str]]:
    if not config.require_token:
        return True, []
    expected = config.token
    if not expected:
        return False, ["token_required_but_not_configured"]
    if (token or "").strip() != expected:
        return False, ["invalid_token"]
    return True, []


def ingest_report(
    *,
    config: DevServerConfig,
    storage: DevServerStorage,
    node_data: dict[str, Any],
    report_data: dict[str, Any],
    auth_token: str | None = None,
) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    if not config.enabled:
        return {
            "code": "DEV_SERVER_REPORT_BLOCKED",
            "node_id": None,
            "report_id": None,
            "redaction_status": None,
            "warnings": warnings,
            "errors": ["dev_server_disabled"],
        }

    lab_mode = str(report_data.get("lab_mode") or node_data.get("lab_mode") or "local_lab")

    if lab_mode == "public_rescue" and not config.public_uploads_allowed:
        return {
            "code": "DEV_SERVER_REPORT_BLOCKED",
            "node_id": None,
            "report_id": None,
            "redaction_status": None,
            "warnings": warnings,
            "errors": ["public_uploads_blocked"],
        }

    if config.mode != "local_lab" and lab_mode == "local_lab":
        return {
            "code": "DEV_SERVER_REPORT_BLOCKED",
            "node_id": None,
            "report_id": None,
            "redaction_status": None,
            "warnings": warnings,
            "errors": ["local_lab_not_active"],
        }

    ok_token, token_errors = _validate_token(config, auth_token)
    if not ok_token:
        if "token_required_but_not_configured" in token_errors:
            return {
                "code": "DEV_SERVER_REPORT_BLOCKED",
                "node_id": None,
                "report_id": None,
                "redaction_status": "review_required",
                "warnings": ["review_required"],
                "errors": token_errors,
            }
        return {
            "code": "DEV_SERVER_REPORT_BLOCKED",
            "node_id": None,
            "report_id": None,
            "redaction_status": None,
            "warnings": warnings,
            "errors": token_errors,
        }

    node_id = str(node_data.get("node_id") or report_data.get("node_id") or "").strip()
    if not node_id:
        node_id = new_id("node")

    existing = storage.load_node(node_id)
    if existing:
        node = merge_node_update(existing, node_data)
    else:
        node = default_dev_node(
            node_id=node_id,
            display_name=str(node_data.get("display_name") or node_id),
            node_kind=str(node_data.get("node_kind") or "unknown"),
            lab_mode=lab_mode,
        )
        node = merge_node_update(node, node_data)

    node["status"] = "online"
    storage.save_node(node)

    report_id = str(report_data.get("report_id") or new_id("report"))
    report = default_dev_report(
        report_id=report_id,
        node_id=node_id,
        report_type=str(report_data.get("report_type") or "manual"),
        lab_mode=lab_mode,
        payload=dict(report_data.get("payload") or {}),
        redaction_status=str(report_data.get("redaction_status") or "raw_lab"),
    )
    for field in ("setuphelfer_version", "rescue_build_id", "evidence_paths", "warnings", "errors"):
        if field in report_data:
            report[field] = report_data[field]

    if lab_mode in ("beta_opt_in", "public_rescue"):
        forbidden = detect_forbidden_sensitive_fields(report.get("payload") or {})
        if forbidden and lab_mode == "public_rescue":
            return {
                "code": "DEV_SERVER_REPORT_BLOCKED",
                "node_id": node_id,
                "report_id": None,
                "redaction_status": None,
                "warnings": warnings,
                "errors": ["public_rescue_forbidden_fields"] + forbidden[:5],
            }

    report, redact_warnings, redact_errors = apply_lab_mode_redaction(report, lab_mode)
    warnings.extend(redact_warnings)
    errors.extend(redact_errors)

    if redact_errors and lab_mode == "public_rescue":
        return {
            "code": "DEV_SERVER_REPORT_BLOCKED",
            "node_id": node_id,
            "report_id": None,
            "redaction_status": report.get("redaction_status"),
            "warnings": warnings,
            "errors": errors,
        }

    if not report.get("created_at"):
        report["created_at"] = utc_now_iso()

    storage.save_report(report)

    storage.append_audit_event({
        "at": utc_now_iso(),
        "event_type": "report_ingested",
        "node_id": node_id,
        "report_id": report_id,
        "lab_mode": lab_mode,
        "redaction_status": report.get("redaction_status"),
    })

    code = "DEV_SERVER_REPORT_ACCEPTED"
    if report.get("redaction_status") == "redacted":
        code = "DEV_SERVER_REPORT_REDACTED_ACCEPTED"

    return {
        "code": code,
        "node_id": node_id,
        "report_id": report_id,
        "redaction_status": report.get("redaction_status"),
        "warnings": warnings,
        "errors": errors,
    }
