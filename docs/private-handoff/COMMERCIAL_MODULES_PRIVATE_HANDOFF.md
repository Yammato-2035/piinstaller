# Commercial Modules — Private Handoff

**Zielgruppe:** Entwicklung im privaten Repository  
**Public Repo:** Nur dieser Handoff + Stubs — **keine Implementierung**

## Module → Private Repo

| Modul | Public erlaubt | Privat erforderlich |
|-------|----------------|---------------------|
| Cloud Backup | Client-Stub, Redaction-Contract | Server, Storage, Billing-Anbindung |
| Cloud Edition Free | Name in Roadmap/Handoff | Feature-Gates, Server |
| Cloud Edition Pro | Name in Roadmap/Handoff | Lizenz, Pro-Features |
| Telemetrieserver | `RESCUE_TELEMETRY_CLIENT_*` Contract | Ingest, DB, Signatur-Secrets |
| Diagnostikserver | Datenkategorien-Doku | Regeln, Auswertung |
| Operator-Dashboard | — | Vollständige UI + API |
| Lizenz/Billing | — | Enforcement, Payment |
| Commercial Blueprints | public-safe Basis-Blueprints | `commercial-*` Profile |

## Bestehende Handoffs (Public)

- `CLOUDSERVER_PRIVATE_REPO_HANDOFF.md`
- `TELEMETRY_INTERNAL_SERVER_HANDOFF.md`
- `DIAGNOSTICS_INTERNAL_SERVER_HANDOFF.md`
- `OPERATOR_DASHBOARD_PRIVATE_HANDOFF.md`
- `PLESK_FREE_VERSION_FUTURE_HANDOFF.md`

## Integration aus Public

Public Client darf:

- Opt-in senden (redacted)
- Lokale Safety-Gates respektieren
- Auf private Endpoints **nicht** hardcoden (nur `.example`)

## Commit-Gate

`./scripts/check-public-private-boundary.sh` — Exit 10–19 blockiert Push.
