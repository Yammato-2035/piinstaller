"""Redaction und sensitive-field guard im Agent vor Upload."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from devserver.redaction import (
    apply_lab_mode_redaction,
    detect_forbidden_sensitive_fields,
    redact_report_for_beta,
)


def detect_sensitive_fields(payload: dict[str, Any]) -> list[str]:
    return detect_forbidden_sensitive_fields(payload)


def redact_for_beta(payload: dict[str, Any]) -> dict[str, Any]:
    report_stub = {"report_type": "inventory", "payload": deepcopy(payload)}
    redacted = redact_report_for_beta(report_stub)
    return redacted.get("payload") or {}


def enforce_mode_redaction(mode: str, report: dict[str, Any]) -> tuple[dict[str, Any], list[str], list[str]]:
    lab_mode = (mode or "").strip()
    if lab_mode == "public_rescue":
        return report, [], ["public_upload_blocked"]

    if lab_mode == "beta_opt_in":
        sensitive = detect_sensitive_fields(report.get("payload") or {})
        out = deepcopy(report)
        redacted = redact_report_for_beta(out)
        warnings = ["sensitive_fields_redacted"] if sensitive else []
        return redacted, warnings, []

    if lab_mode == "local_lab":
        out = deepcopy(report)
        sensitive = detect_sensitive_fields(out.get("payload") or {})
        warnings = [f"sensitive_field_present:{f}" for f in sensitive[:10]] if sensitive else []
        out["redaction_status"] = "raw_lab"
        return out, warnings, []

    out, warnings, errors = apply_lab_mode_redaction(deepcopy(report), lab_mode)
    return out, warnings, errors
