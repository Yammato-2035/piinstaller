# Setuphelfer — Public/Private Strategie

**Stand:** 2026-06-16  
**Repository-Kontext:** Public-Repo = Open Source / Transparenz; Private-Repo = proprietäre Editionen und Betriebsdienste.

Diese Matrix beschreibt **wo** Code, Contracts und Betrieb liegen — **ohne** grüne Produktions-Statusbehauptung.

---

## Produkt- und Edition-Matrix

| Komponente | Public-Repo | Private-Repo | Contract / Schnittstelle | Implementierungsstatus |
|------------|-------------|--------------|---------------------------|------------------------|
| **Core** (Backup, Restore, Verify, Facades) | ✅ Vollständige Fachlogik | — (nutzt Public) | `storage_facade`, `mount_facade`, `safety_facade` | **Aktiv** — Monolith-Entkopplung läuft |
| **Rettungsstick** (Rescue) | ✅ Stick, ISO, Agent-Stubs, Fleet-Lab | Optional: erweiterte Operator-Tools | Rescue-Agent-Contracts, `NOTIFICATION_EVENT_CONTRACT` | **Aktiv** — BR-001-Track |
| **Telemetry Client Contract** | ✅ `telemetry_client_contract.py`, OpenAPI-Stub | — | Opt-in, Redaction-before-send | **Contract aktiv** — kein Pflicht-Send |
| **Telemetry Server** | ❌ Nur Doku/Handoff | ✅ Ingest, Store, Admin-API | Spiegelt Client-Envelope | **Nicht im Public-Repo** |
| **Diagnostics Server** | ❌ Plan-only Client-Contract | ✅ Matcher, Session-Plane, KB-Ingest | `diagnostic_finding_contract` | **Konzept** (DS.1) — siehe [`DIAGNOSTIC_SERVER_ARCHITECTURE_DS1.md`](DIAGNOSTIC_SERVER_ARCHITECTURE_DS1.md) |
| **Cloudserver Edition** | ❌ Stubs + Grenzdoku | ✅ Snapshots, inkrementell, DB-Hooks | `docs/api/cloud_public_contracts_openapi.yaml` | **Zurückgestellt** — separater Track |
| **Operator Dashboard** | ❌ Handoff only | ✅ UI + APIs | Audit/Notification-Spiegel (read) | **Nicht im Public-Repo** |
| **License / Billing** | ❌ Keine Enforcement-Logik | ✅ Abo, Rechnung, Feature-Gates | Feature-Flags via private API | **Nicht im Public-Repo** |
| **Plesk Free** | ❌ Nur Zukunftsplan | ✅ (später) Katalog/Hosting-Integration | TBD — nach Cloudserver-Reife | **Zukunft** — siehe [`PLESK_FREE_VERSION_FUTURE_PLAN.md`](PLESK_FREE_VERSION_FUTURE_PLAN.md) |
| **HostPilot** | ❌ Roadmap-Referenz only | ✅ (geplant) Serverguide/Automation | TBD | **Keine belastbare operative Quelle** im Public-Repo |

---

## Strategische Prinzipien

1. **Contracts first:** Öffentliche Repos definieren Form und Grenzen; private Repos implementieren.  
2. **One-way dependency:** Public → Private ist verboten.  
3. **Recovery-Core vor Cloud:** Cloudserver, Plesk Free und HostPilot werden nicht vor stabilem Backup/Restore/Rescue priorisiert (Roadmap-Entscheidung).  
4. **Opt-in Telemetrie:** Kein stiller Upload; Consent und Redaction sind Client-Pflicht.  
5. **Kein Security-through-obscurity:** Public-Repo enthält bewusst keine Secrets; Schutz durch Private-Repo-Trennung und Gates.

---

## Release- und Betriebsmodell

| Phase | Public | Private |
|-------|--------|---------|
| Entwicklung | Facades, Tests, Doku | Server, Dashboard, Billing |
| CI | Boundary-Gates, Unit/Contract-Tests | Integration gegen Contracts |
| Beta | Desktop/Rescue aus Public | Operator-Services optional parallel |
| Produktion | Pakete (deb/rpm/Tauri) aus Public-Build | Hosted Services nur privat |

---

## Handoff-Pfade

| Thema | Handoff-Dokument |
|-------|------------------|
| Cloudserver Edition | [`docs/private-handoff/CLOUDSERVER_PRIVATE_REPO_HANDOFF.md`](../private-handoff/CLOUDSERVER_PRIVATE_REPO_HANDOFF.md) |
| Telemetrie-Server | [`docs/private-handoff/TELEMETRY_INTERNAL_SERVER_HANDOFF.md`](../private-handoff/TELEMETRY_INTERNAL_SERVER_HANDOFF.md) |
| Diagnostikserver | [`docs/private-handoff/DIAGNOSTICS_INTERNAL_SERVER_HANDOFF.md`](../private-handoff/DIAGNOSTICS_INTERNAL_SERVER_HANDOFF.md) |
| Operator Dashboard | [`docs/private-handoff/OPERATOR_DASHBOARD_PRIVATE_HANDOFF.md`](../private-handoff/OPERATOR_DASHBOARD_PRIVATE_HANDOFF.md) |
| Plesk Free (Zukunft) | [`docs/private-handoff/PLESK_FREE_VERSION_FUTURE_HANDOFF.md`](../private-handoff/PLESK_FREE_VERSION_FUTURE_HANDOFF.md) |

---

## Status-Hinweis

Diese Strategie ist **normativ** für Repository-Grenzen. Einzelne Produkttracks (Cloudserver, Plesk Free, HostPilot) sind bewusst **nicht** als „fertig“ oder „grün“ markiert.
