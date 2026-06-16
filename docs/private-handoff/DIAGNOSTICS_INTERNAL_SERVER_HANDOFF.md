# Diagnostikserver — Internal Server Handoff

**Klassifizierung:** PROPRIETARY · **Nur privates Repository**  
**Stand:** 2026-06-16  
**Public-Referenz:** [`docs/architecture/DIAGNOSTIC_SERVER_ARCHITECTURE_DS1.md`](../architecture/DIAGNOSTIC_SERVER_ARCHITECTURE_DS1.md)

---

## 1. Zweck

Übergabe für den **zentralen Diagnostikserver** (Ingest Plane, Session Plane, Analysis Plane, Knowledge Plane). Lokale `/api/diagnostics` im Public-Repo bleibt **Client/Lab**; interne Matcher und KB-Korrelation sind **private**.

---

## 2. Scope

| Plane | Private Funktion |
|-------|------------------|
| Ingest | Telemetrie-, Agent- und Session-Signale |
| Session | Einheitliches `session_id` / `run_id` Modell |
| Analysis | Interne Regeln, Matcher, Scoring |
| Knowledge | KB/FAQ-Korrelation, Learning Loop (operator-gesteuert) |

**Public-Contract für Ausgaben:** `backend/core/diagnostic_finding_contract.py` — immer `plan_only`, `execute_allowed: false`.

---

## 3. Grenze zu Public-Diagnostics

| Aspekt | Public (`setuphelfer.diagnostics_client`) | Private (`setuphelfer.diagnostics_server`) |
|--------|-------------------------------------------|--------------------------------------------|
| Regeln | Dokumentierte Cases, lokale Engines | Interne Matcher, proprietäre Heuristiken |
| Execute | Verboten | Nur im Private-Operator-Kontext (nicht im OSS-Build) |
| OpenAPI | `diagnostics_client_contract_openapi.yaml` | Admin/OpenAPI nur privat |

---

## 4. Verboten im Public-Repo

- `backend/diagnostics_server/`
- `backend/internal_diagnostics/`
- `INTERNAL_DIAGNOSTIC_RULE` (Gate-Begriff)
- Unredigierte Kunden-Logs in Evidence

---

## 5. Eingehende Daten (minimal)

- Redacted Signals (via `redaction_contract`)
- `DiagnosticFinding`-kompatible Erweiterungen nur mit Version-Bump
- Session-Metadaten ohne PII

Beispiel-Ingest-Host (Doku): `https://diagnose.internal.setuphelfer.example/v1/ingest`

---

## 6. Ausgehende Daten

- Findings im Public-Contract-Format
- Evidence-Refs als opaque IDs — keine absoluten Host-Pfade in Public-Exports
- Audit-Events (`audit_event_contract`) für Operator

---

## 7. Private Repository-Struktur (Soll)

```text
backend/
  diagnostics_server/
    ingest_plane.py
    session_plane.py
    analysis_plane.py
    knowledge_plane.py
tests/
  test_finding_contract_compliance.py
docs/
  internal/           # nicht nach Public spiegeln
```

---

## 8. Abnahmekriterien

- [ ] Alle extern sichtbaren Findings bestehen `diagnostic_finding_contract`-Tests
- [ ] Kein Auto-Repair über Public-API
- [ ] DS.1-Architektur-Planes dokumentiert im Private-Repo
- [ ] Legal: Zweckbindung Diagnose vs. Telemetrie geklärt

---

## 9. Referenzen

- [`DIAGNOSTIC_SERVER_ARCHITECTURE_DS1.md`](../architecture/DIAGNOSTIC_SERVER_ARCHITECTURE_DS1.md)
- [`MODULE_CONTRACTS.md`](../architecture/MODULE_CONTRACTS.md)
- [`docs/api/diagnostics_client_contract_openapi.yaml`](../api/diagnostics_client_contract_openapi.yaml)
