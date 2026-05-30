"""Redaction und Beta-Vorbereitung für Development-Server-Berichte."""

from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from typing import Any

_SENSITIVE_KEYS = frozenset({
    "hostname",
    "username",
    "user_name",
    "real_name",
    "email",
    "mac_address",
    "mac",
    "ip_address",
    "ip",
    "disk_serial",
    "serial",
    "filesystem_uuid",
    "uuid",
    "windows_product_id",
    "product_id",
    "ssh_key",
    "private_key",
    "public_key",
    "token",
    "access_token",
    "wlan_ssid",
    "ssid",
    "browser_path",
    "profile_path",
    "document_filename",
    "auth_ref",
    "password",
})

_MAC_RE = re.compile(r"([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}")
_IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def hash_sensitive_value(value: str, salt_scope: str) -> str:
    raw = f"{salt_scope}:{value}".encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()[:16]


def _redact_string(value: str, *, salt_scope: str, redact_ip: bool) -> str:
    out = value
    out = _EMAIL_RE.sub(lambda m: hash_sensitive_value(m.group(0), salt_scope), out)
    out = _MAC_RE.sub(lambda m: hash_sensitive_value(m.group(0), salt_scope), out)
    if redact_ip:
        out = _IP_RE.sub(lambda m: hash_sensitive_value(m.group(0), salt_scope), out)
    return out


def _walk_redact(obj: Any, *, salt_scope: str, redact_ip: bool) -> Any:
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            key_l = str(k).lower()
            if key_l in _SENSITIVE_KEYS:
                if isinstance(v, str) and v:
                    out[k] = hash_sensitive_value(v, f"{salt_scope}:{key_l}")
                elif v is not None:
                    out[k] = "[redacted]"
                continue
            out[k] = _walk_redact(v, salt_scope=salt_scope, redact_ip=redact_ip)
        return out
    if isinstance(obj, list):
        return [_walk_redact(x, salt_scope=salt_scope, redact_ip=redact_ip) for x in obj]
    if isinstance(obj, str):
        return _redact_string(obj, salt_scope=salt_scope, redact_ip=redact_ip)
    return obj


def detect_forbidden_sensitive_fields(payload: dict[str, Any]) -> list[str]:
    found: list[str] = []

    def _scan(obj: Any, path: str) -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                p = f"{path}.{k}" if path else k
                if str(k).lower() in _SENSITIVE_KEYS and isinstance(v, str) and v.strip():
                    if not str(v).startswith("sha256:"):
                        found.append(p)
                _scan(v, p)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                _scan(item, f"{path}[{i}]")

    _scan(payload, "")
    return found


def redact_hardware_inventory(payload: dict[str, Any]) -> dict[str, Any]:
    return _walk_redact(deepcopy(payload), salt_scope="hardware", redact_ip=True)


def redact_storage_topology(payload: dict[str, Any]) -> dict[str, Any]:
    data = _walk_redact(deepcopy(payload), salt_scope="storage", redact_ip=False)
    if isinstance(data, dict):
        data.pop("serial", None)
        for dev in data.get("block_devices") or []:
            if isinstance(dev, dict):
                dev.pop("serial", None)
    return data


def redact_boot_profile(payload: dict[str, Any]) -> dict[str, Any]:
    return _walk_redact(deepcopy(payload), salt_scope="boot", redact_ip=True)


def redact_report_for_beta(report: dict[str, Any]) -> dict[str, Any]:
    out = deepcopy(report)
    payload = out.get("payload")
    if isinstance(payload, dict):
        rtype = str(out.get("report_type") or "")
        if rtype == "inventory" or "cpu" in payload or "memory" in payload:
            out["payload"] = redact_hardware_inventory(payload)
        elif rtype == "storage" or "block_devices" in payload:
            out["payload"] = redact_storage_topology(payload)
        elif rtype == "boot" or "detected_bootloaders" in payload:
            out["payload"] = redact_boot_profile(payload)
        else:
            out["payload"] = _walk_redact(payload, salt_scope="report", redact_ip=True)
    out["redaction_status"] = "redacted"
    return out


def apply_lab_mode_redaction(report: dict[str, Any], lab_mode: str) -> tuple[dict[str, Any], list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    mode = (lab_mode or "").strip()

    if mode == "local_lab":
        out = deepcopy(report)
        out["redaction_status"] = "raw_lab"
        return out, warnings, errors

    if mode == "beta_opt_in":
        forbidden = detect_forbidden_sensitive_fields(report.get("payload") or {})
        if forbidden:
            warnings.append("forbidden_fields_redacted")
        out = redact_report_for_beta(report)
        return out, warnings, errors

    if mode == "public_rescue":
        forbidden = detect_forbidden_sensitive_fields(report.get("payload") or {})
        if forbidden:
            errors.append("public_rescue_forbidden_fields")
        out = deepcopy(report)
        out["payload"] = {"summary": "public_safe_minimal", "report_type": out.get("report_type")}
        out["redaction_status"] = "not_required"
        return out, warnings, errors

    errors.append("unknown_lab_mode")
    return report, warnings, errors
