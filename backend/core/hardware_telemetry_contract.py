"""
Public telemetry contract ``hardware_inventory_summary_v1``.

PI-RS-HW-COMPAT-PROVISION-001 Phase 16.

Strict allowlist model (spec): the payload builder below only ever *copies in*
fields from the explicit allowlist — it never does a generic deep-copy of raw
device rows. This is a deliberately narrower/separate contract from the
existing rescue-assessment telemetry (see
``docs/evidence/rescue/hardware-compat-001/HARDWARE_DISCOVERY_IST_AUDIT.md``);
it reuses ``core.telemetry_redaction_contract`` as a defense-in-depth second
pass, it does not replace it.

Allowed (spec PHASE 16):
  platform class, CPU vendor/model family, architecture, GPU vendor/model
  class, per-class device counts, driver/firmware status counts, Raspberry Pi
  model family, rescue payload version, kernel version, known issue codes,
  correlation id, evidence hashes.

Forbidden: serial numbers, MAC addresses, IP addresses, full EDID, printer/
scanner/USB-stick serials, user/host names, raw unique device identifiers.
"""

from __future__ import annotations

from typing import Any

from core.telemetry_redaction_contract import redact_string

HARDWARE_TELEMETRY_CONTRACT_VERSION = 1
HARDWARE_TELEMETRY_SCHEMA_ID = "hardware_inventory_summary_v1"

_FORBIDDEN_KEY_FRAGMENTS = (
    "serial",
    "mac_address",
    "mac",
    "ip_address",
    "edid",
    "hostname",
    "username",
    "user_name",
    "device_id",
    "raw_id",
)

# Structured, controlled-vocabulary fields whose values are legitimately allowed
# to look like a dotted-quad (e.g. Setuphelfer's own X.Y.Z.W version scheme,
# "1.10.6.0") without being an IP address — excluded from the IP-shape check.
_DOTTED_VERSION_LIKE_KEYS = frozenset({"rescue_payload_version", "kernel_version"})


def build_hardware_inventory_summary_v1(
    *,
    inventory_summary: dict[str, Any],
    cpu_vendor: str | None = None,
    cpu_model_family: str | None = None,
    gpu_vendor: str | None = None,
    gpu_model_class: str | None = None,
    raspberry_pi_model_family: str | None = None,
    rescue_payload_version: str | None = None,
    kernel_version: str | None = None,
    known_issue_codes: list[str] | None = None,
    correlation_id: str | None = None,
    evidence_hashes: list[str] | None = None,
) -> dict[str, Any]:
    """Build an allowlist-only public telemetry payload.

    ``inventory_summary`` should be ``hardware_inventory.build_hardware_inventory_summary(...)``
    output (already aggregate counts, no raw device rows) — this function copies
    only the specific aggregate fields it needs, never the whole dict blindly.
    """
    payload: dict[str, Any] = {
        "schema_id": HARDWARE_TELEMETRY_SCHEMA_ID,
        "contract_version": HARDWARE_TELEMETRY_CONTRACT_VERSION,
        "platform_class": inventory_summary.get("platform_class"),
        "architecture": inventory_summary.get("architecture"),
        "is_raspberry_pi": bool(inventory_summary.get("is_raspberry_pi")),
        "raspberry_pi_model_family": raspberry_pi_model_family,
        "cpu_vendor": cpu_vendor,
        "cpu_model_family": cpu_model_family,
        "gpu_vendor": gpu_vendor,
        "gpu_model_class": gpu_model_class,
        "device_count_by_class": dict(inventory_summary.get("device_count_by_class") or {}),
        "device_count_by_operational_status": dict(inventory_summary.get("device_count_by_operational_status") or {}),
        "rescue_payload_version": rescue_payload_version,
        "kernel_version": kernel_version,
        "known_issue_codes": list(known_issue_codes or []),
        "correlation_id": correlation_id,
        "evidence_hashes": list(evidence_hashes or []),
    }
    # Defense-in-depth: redact any *descriptive* string value that still looks like
    # an IP/MAC/hostname/serial/email/token even though only allowlisted fields
    # were copied. Deliberately excludes structured identifiers (version strings,
    # kernel version, correlation_id) — those are dotted/controlled-vocabulary
    # values (e.g. "1.10.6.0") that the generic IP-shaped regex would otherwise
    # false-positive on.
    _descriptive_fields = (
        "cpu_vendor",
        "cpu_model_family",
        "gpu_vendor",
        "gpu_model_class",
        "raspberry_pi_model_family",
    )
    for key in _descriptive_fields:
        value = payload.get(key)
        if isinstance(value, str):
            payload[key] = redact_string(value)
    return payload


def validate_hardware_telemetry_payload(payload: dict[str, Any]) -> list[str]:
    """Hard-block check: return violation codes (empty == safe to send).

    Spec requirement: "Telemetrie mit Seriennummer muss blockiert oder redigiert
    werden" — this scans both forbidden *key names* and forbidden *value shapes*
    (already-redacted placeholders are fine; raw-looking serials/MACs/IPs are not).
    """
    import re

    violations: list[str] = []
    serial_like = re.compile(r"\b(?=[A-Z0-9]*[A-Z])(?=[A-Z0-9]*[0-9])[A-Z0-9]{10,32}\b")
    mac_like = re.compile(r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b")
    ip_like = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")

    def walk(obj: Any, key: str = "") -> None:
        lk = key.lower()
        if any(fragment in lk for fragment in _FORBIDDEN_KEY_FRAGMENTS) and obj not in (None, "", []):
            violations.append(f"forbidden_key:{key}")
            return
        if isinstance(obj, dict):
            for k, v in obj.items():
                walk(v, str(k))
        elif isinstance(obj, list):
            for item in obj:
                walk(item, key)
        elif isinstance(obj, str):
            if "[REDACTED:" in obj:
                return
            if serial_like.search(obj):
                violations.append(f"serial_like_value:{key}")
            if mac_like.search(obj):
                violations.append(f"mac_like_value:{key}")
            if key not in _DOTTED_VERSION_LIKE_KEYS and ip_like.search(obj):
                violations.append(f"ip_like_value:{key}")

    walk(payload)
    return violations


def build_hardware_telemetry_contract_diagnostics() -> dict[str, Any]:
    return {
        "contract_version": HARDWARE_TELEMETRY_CONTRACT_VERSION,
        "schema_id": HARDWARE_TELEMETRY_SCHEMA_ID,
        "module": "core.hardware_telemetry_contract",
        "allowlist_only": True,
        "network_upload_performed": False,
    }


__all__ = [
    "HARDWARE_TELEMETRY_CONTRACT_VERSION",
    "HARDWARE_TELEMETRY_SCHEMA_ID",
    "build_hardware_inventory_summary_v1",
    "validate_hardware_telemetry_payload",
    "build_hardware_telemetry_contract_diagnostics",
]
