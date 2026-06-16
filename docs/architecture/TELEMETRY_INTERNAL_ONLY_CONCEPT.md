# Telemetrie — Internal-Only Konzept

**Stand:** 2026-06-16  
**Status:** Konzept + Client-Contract im Public-Repo · Server **internal-only**

---

## Zielbild

Setuphelfer unterscheidet strikt zwischen:

1. **Telemetry Client** (public) — lokale Sammlung, Redaction, Opt-in, Validierung  
2. **Telemetry Server** (private) — Ingest, Speicherung, Aggregation, Operator-Zugriff

Endanwender und öffentliche Builds **dürfen** den Server-Code weder sehen noch ausliefern.

---

## Datenfluss (konzeptionell)

```text
[Lokales Setuphelfer]
        │
        ├─ Opt-in OFF ──► kein Send
        │
        └─ Opt-in ON
              ├─ redaction_contract (lokal)
              ├─ telemetry_client_contract (Envelope)
              └─ HTTPS ──► telemetry.internal.setuphelfer.example  (nur Beispiel-Domain)
                                    │
                                    ▼
                         [Private Telemetry Server]
                         Ingest · Store · Retention · Admin
```

---

## Public-Contract (`telemetry_client_contract.py`)

| Feld / Regel | Bedeutung |
|--------------|-----------|
| `opt_in_state` | `disabled` \| `enabled` \| `pending_consent` |
| `redaction_applied` | Muss `true` sein vor Send |
| `local_preview_ok` | Nutzer/Admin hat redigierte Vorschau bestätigt |
| `data_categories` | Explizite Kategorien (Version, Runtime-Health, …) |
| Kein Server-URL in `to_public_dict()` | `endpoint_configured: false` in Preview |

Validierung: `validate_client_envelope()` — u. a. Blockade bei internen Domains ohne `.example`.

---

## Was der Server darf (nur privat dokumentiert)

- HMAC/Token-Prüfung am Ingest  
- Retention und Löschfristen  
- Aggregation für Operator-Dashboard  
- Korrelation mit Diagnostik-Sessions (private Schnittstelle)

**Nicht** im Public-Repo: Signing-Keys, Store-Schema, interne Admin-Routen.

---

## Trennung von anderen Kanälen

| Kanal | Zweck | Repo |
|-------|-------|------|
| Rescue-Telemetrie-Ingest (Lab) | Stick/Fleet-Evidence | Public (begrenzt, profil-gated) |
| Dev-Server-Ingest | Entwickler-Maschinen | Public (Lab) |
| Zentraler Telemetry Server | Produkt-/Fleet-Aggregation | **Private** |

Siehe auch: `LOCAL_LAB_TELEMETRY`-Trennung in Rescue-/DCC-Dokumentation.

---

## Rechtliche Vorgaben (Verweis)

- [`docs/legal/TELEMETRY_CONSENT_REQUIRED_ITEMS_DE.md`](../legal/TELEMETRY_CONSENT_REQUIRED_ITEMS_DE.md)  
- [`docs/legal/DATA_DELETION_RETENTION_CONCEPT_DRAFT_DE.md`](../legal/DATA_DELETION_RETENTION_CONCEPT_DRAFT_DE.md)

---

## Handoff

[`docs/private-handoff/TELEMETRY_INTERNAL_SERVER_HANDOFF.md`](../private-handoff/TELEMETRY_INTERNAL_SERVER_HANDOFF.md)

---

## OpenAPI (public-safe)

[`docs/api/telemetry_client_contract_openapi.yaml`](../api/telemetry_client_contract_openapi.yaml)
