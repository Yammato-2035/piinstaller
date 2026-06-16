# Telemetrie — Nur intern (Server) (DE)

**Stand:** 2026-06-16  
**Kurzfassung** — siehe [`docs/architecture/TELEMETRY_INTERNAL_ONLY_CONCEPT.md`](../../architecture/TELEMETRY_INTERNAL_ONLY_CONCEPT.md)

---

## Zwei Ebenen

| Ebene | Repository | Inhalt |
|-------|------------|--------|
| **Client** | Public | Sammlung, Redaction, Opt-in, Validierung |
| **Server** | Private | Ingest, Store, Retention, Operator-Zugriff |

---

## Nutzerperspektive

1. Telemetrie ist **standardmäßig aus** oder wartet auf Einwilligung (`pending_consent`).
2. Vor dem Senden: **redigierte Vorschau** (`redaction_contract`).
3. Nur explizit gewählte **Datenkategorien** werden übertragen.
4. Widerruf jederzeit möglich.

---

## Entwicklerperspektive

- Implementierung: `backend/core/telemetry_client_contract.py`
- Tests: `backend/tests/test_telemetry_client_contract_v1.py`
- OpenAPI: `docs/api/telemetry_client_contract_openapi.yaml`
- **Kein** Server-Code im Public-Repo (`backend/telemetry_server/` verboten)

---

## Rechtliches

- [`docs/legal/TELEMETRY_CONSENT_REQUIRED_ITEMS_DE.md`](../../legal/TELEMETRY_CONSENT_REQUIRED_ITEMS_DE.md)
- [`docs/legal/DATA_DELETION_RETENTION_CONCEPT_DRAFT_DE.md`](../../legal/DATA_DELETION_RETENTION_CONCEPT_DRAFT_DE.md)

---

## Handoff (privat)

[`docs/private-handoff/TELEMETRY_INTERNAL_SERVER_HANDOFF.md`](../../private-handoff/TELEMETRY_INTERNAL_SERVER_HANDOFF.md)
