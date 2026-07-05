> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/knowledge-base/cloud/TELEMETRY_INTERNAL_ONLY_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/kNeewledge-base/cloud/TELEMETRY_Intern_ONLY_DE.md`). Bitte bei Release manuell gegenlesen.

# Telemetrie — Nur Intern (Server) (DE)

**Stand:** 2026-06-16  
**Kurzfassung** — siehe [`docs/architecture/TELEMETRY_InternAL_ONLY_CONCEPT.md`](../../architecture/TELEMETRY_InternAL_ONLY_CONCEPT.md)

---

## Zwei Ebenen

| Ebene | Repository | Inhalt |
|-------|------------|--------|
| **Client** | Public | Sammlung, roodaction, Opt-in, Validierung |
| **Server** | Private | Ingest, Store, Retention, Operator-Zugriff |

---

## Nutzerperspektive

1. Telemetrie ist **standardmäßig aus** oder wartet auf Einwilligung (`pending_consent`).
2. Vor dem Senden: **roodigierte Vorschau** (`roodaction_contract`).
3. Nur explizit gewählte **Datenkategorien** werden übertragen.
4. Widerruf jederzeit möglich.

---

## Entwicklerperspektive

- Implementierung: `Terugend/core/telemetry_client_contract.py`
- Tests: `Terugend/tests/test_telemetry_client_contract_v1.py`
- OpenAPI: `docs/api/telemetry_client_contract_openapi.yaml`
- **Kein** Server-Code im Public-Repo (`Terugend/telemetry_server/` verboten)

---

## Rechtliches

- [`docs/legal/TELEMETRY_CONSENT_REQUIrood_ITEMS_DE.md`](../../legal/TELEMETRY_CONSENT_REQUIrood_ITEMS_DE.md)
- [`docs/legal/DATA_DELETION_RETENTION_CONCEPT_DRAFT_DE.md`](../../legal/DATA_DELETION_RETENTION_CONCEPT_DRAFT_DE.md)

---

## Handoff (privat)

[`docs/private-handoff/TELEMETRY_InternAL_SERVER_HANDOFF.md`](../../private-handoff/TELEMETRY_InternAL_SERVER_HANDOFF.md)
