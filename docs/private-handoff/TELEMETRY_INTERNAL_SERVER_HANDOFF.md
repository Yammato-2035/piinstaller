# Telemetrie-Server — Internal Server Handoff

**Klassifizierung:** PROPRIETARY · **Nur privates Repository**  
**Stand:** 2026-06-16  
**Public-Referenz:** [`docs/architecture/TELEMETRY_INTERNAL_ONLY_CONCEPT.md`](../architecture/TELEMETRY_INTERNAL_ONLY_CONCEPT.md)

---

## 1. Zweck

Implementierungs- und Betriebsübergabe für den **internen Telemetrie-Server** (Ingest, Speicher, Retention, Admin). Der **Client-Contract** bleibt im Public-Repo.

---

## 2. Scope

| Komponente | Beschreibung |
|------------|--------------|
| Ingest API | Annahme von `TelemetryClientEnvelope` (nach Client-Validierung) |
| Auth | Token/HMAC — Schlüssel **nur privat** |
| Store | Zeitreihen/Events, partitioniert nach `data_categories` |
| Retention | Löschfristen gemäß Legal-Konzept |
| Admin API | Read-only für Operator-Dashboard (privat) |
| Export | Anonymisierte Aggregate — keine Roh-PII |

**Nicht:** Rescue-Lab-Ingest, Dev-Server — bleiben Public-Lab-Pfade mit eigenen Profil-Gates.

---

## 3. Public Contract (einzige eingehende Form)

Quelle: `backend/core/telemetry_client_contract.py`

Pflicht vor Persistenz:

- `opt_in_state == enabled`
- `redaction_applied == true`
- `local_preview_ok == true`
- Keine internen Domains in `payload` (Client-Validator spiegeln)

OpenAPI: `docs/api/telemetry_client_contract_openapi.yaml`  
Beispiel-Host: `https://telemetry.internal.setuphelfer.example/v1/report`

---

## 4. Verboten im Public-Repo

- `backend/telemetry_server/`
- `backend/internal_telemetry/`
- `TELEMETRY_SERVER_SECRET`, `TELEMETRY_SIGNING_PRIVATE_KEY`
- Produktions-Ingest-URLs

Gate: `scripts/check-public-private-boundary.sh` (Exit 11 bei Verstoß)

---

## 5. Private Repository-Struktur (Soll)

```text
backend/
  telemetry_server/
    ingest.py
    store.py
    retention.py
    admin_read_api.py
infra/
  staging/          # kein deploy/production im Public-Repo
tests/
  test_ingest_contract_compliance.py
```

---

## 6. Integration

| System | Richtung | Daten |
|--------|----------|-------|
| Setuphelfer Client | → Server | Redacted Envelope |
| Operator Dashboard | ← Server | Aggregate, keine Secrets |
| Diagnostics Server | ↔ | Session-Korrelation (privat) |

---

## 7. Betrieb

- [ ] TLS für alle Endpunkte
- [ ] Rate-Limiting pro Installations-ID (pseudonym)
- [ ] Monitoring ohne Payload-Logging in Klartext
- [ ] Incident-Runbook bei Datenleck-Verdacht
- [ ] Regelmäßige Lösch-Jobs (siehe Legal-Draft)

---

## 8. Abnahme

- [ ] Contract-Compliance-Tests gegen Public-Envelope
- [ ] Consent-Flow dokumentiert (`TELEMETRY_CONSENT_REQUIRED_ITEMS_DE.md`)
- [ ] Pen-Test Ingest-Auth
- [ ] Kein Go-Live ohne AVV/DPA für gehostete Region

---

## 9. Referenzen

- [`TELEMETRY_CONSENT_REQUIRED_ITEMS_DE.md`](../legal/TELEMETRY_CONSENT_REQUIRED_ITEMS_DE.md)
- [`DATA_DELETION_RETENTION_CONCEPT_DRAFT_DE.md`](../legal/DATA_DELETION_RETENTION_CONCEPT_DRAFT_DE.md)
- [`TELEMETRY_INTERNAL_SERVER_HANDOFF.md`](TELEMETRY_INTERNAL_SERVER_HANDOFF.md) (dieses Dokument)
