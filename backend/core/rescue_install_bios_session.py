"""Guided BIOS session — read-only compare + checklist (PI-RS-INSTALL-ASSISTANT-001).

No BootNext, no flash. Optional BootNext is lab-only and out of A4 scope.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from core.rescue_bios_official_compare import check_latest_official_bios

CONTRACT_VERSION = 1
SCHEMA_VERSION = 1

CHECKLIST_DE = [
    "Netzteil anschließen und Batterie prüfen",
    "Aktuelle BIOS-Version notieren (nur lesen)",
    "Offizielle Support-Seite des Herstellers öffnen",
    "Neueste offizielle Version mit Ist-Stand vergleichen",
    "BitLocker-/Wiederherstellungsschlüssel bereithalten falls Windows vorhanden",
    "Secure Boot / TPM Auswirkungen lesen — nicht ändern ohne Auftrag",
    "Kein Auto-Flash; kein BootNext in dieser Session",
    "Ergebnis als Evidence exportieren",
]

CHECKLIST_EN = [
    "Connect AC power and check battery",
    "Note installed BIOS version (read-only)",
    "Open manufacturer official support page",
    "Compare latest official version to installed",
    "Have BitLocker recovery key ready if Windows present",
    "Review Secure Boot / TPM impact — do not change without order",
    "No auto-flash; no BootNext in this session",
    "Export result as evidence",
]


def build_bios_session(
    *,
    machine: Mapping[str, Any],
    online: bool = True,
    locale: str = "de",
    skip_reason: str | None = None,
) -> dict[str, Any]:
    compare = check_latest_official_bios(machine=machine, online=online)
    checklist = CHECKLIST_DE if locale.startswith("de") else CHECKLIST_EN
    skipped = bool(skip_reason)
    return {
        "schema_version": SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "mode": "read_only",
        "automatic_flash_allowed": False,
        "boot_next_allowed": False,
        "skipped": skipped,
        "skip_reason": skip_reason,
        "compare": compare,
        "checklist": checklist,
        "locale": locale,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "blocks_mint_dry_run": False,
    }


def export_bios_session_evidence(session: Mapping[str, Any]) -> dict[str, Any]:
    compare = session.get("compare") if isinstance(session.get("compare"), Mapping) else {}
    return {
        "contract": "bios_session_evidence_v1",
        "mode": "read_only",
        "automatic_flash_allowed": False,
        "boot_next_allowed": False,
        "skipped": session.get("skipped"),
        "skip_reason": session.get("skip_reason"),
        "installed_version": compare.get("installed_version"),
        "latest_official_version": compare.get("latest_official_version"),
        "compare_status": compare.get("status"),
        "vendor": compare.get("vendor"),
        "exact_model": compare.get("exact_model"),
        "official_support_url": compare.get("official_support_url"),
        "checklist_count": len(list(session.get("checklist") or [])),
        "exported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
