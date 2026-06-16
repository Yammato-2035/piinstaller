# Cloudserver Edition — Private Repository Handoff

**Klassifizierung:** PROPRIETARY · **Nur privates Repository**  
**Stand:** 2026-06-16  
**Public-Referenz:** [`docs/architecture/CLOUDSERVER_EDITION_PRIVATE_BOUNDARY.md`](../architecture/CLOUDSERVER_EDITION_PRIVATE_BOUNDARY.md)

---

## 1. Zweck dieses Dokuments

Übergabe-Checkliste für die Implementierung der **Cloudserver Edition** in einem **separaten, nicht öffentlichen** Git-Repository. Enthält **keine** Implementierung — nur Anforderungen, Grenzen und Abnahmekriterien.

---

## 2. Scope (Private)

| In Scope | Out of Scope (bleibt Public) |
|----------|------------------------------|
| Snapshot-Provider, inkrementelle Backups | Core-Facades (`storage_facade`, `mount_facade`, `safety_facade`) |
| Cloud-Metadaten-Store, DB-Hooks | Rettungsstick-Produktpfad |
| Feature-Gates gekoppelt an Lizenz | Open-Source Desktop-Build |
| Operator-sichtbare Cloud-Jobs | Telemetrie-Server-Ingest (eigenes Handoff) |

---

## 3. Repository-Anforderungen

- [ ] Privates Git-Remote (nicht `PUBLIC` auf GitHub)
- [ ] Zugriff nur für autorisierte Maintainer
- [ ] CI mit `./scripts/check-private-import-boundaries.sh` (oder Äquivalent)
- [ ] Kein Push von `backend/cloudserver_*` in das Public-Repo
- [ ] Secrets in Secret-Manager / CI-Vault — **nicht** im Git-Tree

---

## 4. Erlaubte Public-Abhängigkeiten

| Public-Artefakt | Nutzung |
|-----------------|---------|
| `storage_facade` | Blockgeräte, Klassifikation |
| `mount_facade` | Readonly-Pläne |
| `safety_facade` | `SafetyContext.cloudserver_future` |
| `telemetry_client_contract` | Opt-in Status-Reports |
| `audit_event_contract` | Job-Audit-Trail |
| `docs/api/cloud_public_contracts_openapi.yaml` | API-Form (Spiegel pflegen) |

**Regel:** Private-Repo darf Public als Submodule, Package oder Copy-on-Release einbinden — Public importiert Private **nie**.

---

## 5. Verzeichnisstruktur (Soll, privat)

```text
backend/
  cloudserver_edition/
    snapshot_provider.py
    incremental_backup.py
    database_hooks.py
    orchestrator.py
  cloudserver_private/
    licensing_hooks.py      # Verweis auf operator_private
tests/
  test_cloudserver_contracts_*.py
docs/
  runbooks/
  architecture/
```

Exakte Namen können angepasst werden — **nicht** in Public-Repo committen.

---

## 6. Schnittstellen zu anderen Private-Modulen

| Partner | Schnittstelle |
|---------|---------------|
| Telemetry Server | Opt-in Envelopes, keine Roh-Logs |
| Diagnostics Server | Session-IDs, plan-only Findings |
| Operator Private | Lizenz-Feature-Flags, Kunden-Metadaten |
| License/Billing | Abo-Status, Quota |

---

## 7. Sicherheit

- Keine Kundendaten in Logs ohne Redaction
- Write-Operationen nur nach `safety_facade`-Validierung
- Keine Echo echter Domains in öffentliche Fehlermeldungen
- Penetrationstest vor Beta mit Cloudserver-Pilotkunden

---

## 8. Abnahmekriterien (vor erstem Private-Deploy)

- [ ] Contract-Tests gegen Public OpenAPI-Stubs grün
- [ ] Boundary-Gate: kein Leak sensibler Pfade in Public-PRs
- [ ] Disaster-Recovery-Runbook für Cloud-Metadaten
- [ ] DPA/AVV mit Hosting-Provider (siehe Legal-Checkliste)
- [ ] Kein „grün“ ohne dokumentierte Hardware-/Cloud-Pilot-Evidence

---

## 9. Rollback

- Feature-Flag `cloudserver_edition_enabled=false` auf Operator-Ebene
- Metadaten-Backup vor Schema-Migration
- Public-Desktop-Builds bleiben unverändert funktionsfähig

---

## 10. Kontakte & Governance

| Rolle | Verantwortung |
|-------|---------------|
| Product Owner | Scope-Freigabe Cloudserver |
| Security | Review Ingest/Store-Grenzen |
| Legal | AVV, Datenklassifikation |
| Public-Repo Maintainer | Contract-Änderungen nur via PR + Version-Bump |

---

## 11. Referenzen (Public, lesbar)

- [`SETUPHELFER_PUBLIC_PRIVATE_STRATEGY.md`](../architecture/SETUPHELFER_PUBLIC_PRIVATE_STRATEGY.md)
- [`MODULE_BOUNDARIES.md`](../architecture/MODULE_BOUNDARIES.md)
- [`docs/runbooks/PRIVATE_REPOSITORY_SETUP_RUNBOOK_DE.md`](../runbooks/PRIVATE_REPOSITORY_SETUP_RUNBOOK_DE.md)

---

*Dieses Dokument ist absichtlich im Public-Repo, beschreibt aber ausschließlich private Implementierungspflichten.*
