"""Consent model for physical rescue E2E telemetry."""

from __future__ import annotations

from typing import Any

from core.rescue_physical_e2e_models import (
    CONSENT_ABORTED,
    CONSENT_GRANTED,
    CONSENT_LOCAL_ONLY,
    ConsentChoice,
)

CONSENT_DIALOG_TEXT_DE = """Der Setuphelfer kann technische Informationen über diesen Testlauf
an den Setuphelfer-Telemetrieserver senden.

Gesendet werden:
- pseudonymisierte Gerätekennung
- Rettungsstick-Version
- Status von Backup, Verify und Restore
- Dateianzahl und Gesamtgröße
- zusammenfassende Prüfsummen
- technische Fehlercodes

Nicht gesendet werden:
- Dateiinhalte
- vollständige Dateinamen
- Benutzernamen
- Passwörter
- Seriennummern
- MAC-Adressen"""

CONSENT_OPTIONS = (
    ("granted", "Zustimmen und senden"),
    ("local_only", "Nur lokal protokollieren"),
    ("aborted", "Abbrechen"),
)


def normalize_consent_choice(raw: str | None) -> ConsentChoice:
    value = (raw or "").strip().lower()
    if value in {"granted", "yes", "accept", "consent_granted"}:
        return CONSENT_GRANTED
    if value in {"local_only", "local", "deny", "no_send"}:
        return CONSENT_LOCAL_ONLY
    return CONSENT_ABORTED


def consent_allows_send(consent: ConsentChoice) -> bool:
    return consent == CONSENT_GRANTED


def build_consent_record(consent: ConsentChoice, *, shown: bool = True) -> dict[str, Any]:
    return {
        "shown": shown,
        "granted": consent == CONSENT_GRANTED,
        "local_only": consent == CONSENT_LOCAL_ONLY,
        "aborted": consent == CONSENT_ABORTED,
        "telemetry_status": "consent_granted" if consent == CONSENT_GRANTED else "consent_not_granted",
        "signature_required": consent == CONSENT_GRANTED,
    }
