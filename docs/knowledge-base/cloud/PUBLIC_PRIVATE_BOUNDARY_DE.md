# Public/Private-Grenze — Cloud & Operator (DE)

**Stand:** 2026-06-16  
**Kurzfassung** für Wissensdatenbank — Details in Architektur-Docs.

---

## Was ist öffentlich?

Das **öffentliche Repository** enthält Setuphelfer **Core**, **Rettungsstick**, **Deploy-Runner**, **Facades** und **öffentliche Contracts**:

- `storage_facade`, `mount_facade`, `safety_facade`
- `telemetry_client_contract` (Client, opt-in)
- `diagnostic_finding_contract` (plan-only)
- OpenAPI-Stubs unter `docs/api/`

---

## Was ist privat?

Diese Teile **dürfen nicht** im Public-Repo implementiert werden:

| Bereich | Kurzbeschreibung |
|---------|------------------|
| Cloudserver Edition | Snapshots, inkrementelle Cloud-Backups |
| Telemetrie-Server | Ingest, Speicher, Admin |
| Diagnostikserver (intern) | Matcher, zentrale Analyse |
| Operator Dashboard | Betriebs-UI für Kunden/Fleet |
| Lizenz / Billing | Abos, Feature-Gates |
| Plesk Free | **Zukunft** — noch nicht umgesetzt |

---

## Goldene Regel

**Public importiert niemals Private.** Private Repositories dürfen öffentliche Contracts importieren.

Gate: `scripts/check-public-private-boundary.sh`

---

## Beispiel-Domains (nur Doku)

- `telemetry.internal.setuphelfer.example`
- `cloud.private.setuphelfer.example`
- `operator.internal.setuphelfer.example`

Keine echten Produktions-Hostnamen in Commits oder Screenshots.

---

## Weiterlesen

- [`docs/architecture/PUBLIC_PRIVATE_MODULE_BOUNDARIES.md`](../../architecture/PUBLIC_PRIVATE_MODULE_BOUNDARIES.md)
- [`docs/architecture/SETUPHELFER_PUBLIC_PRIVATE_STRATEGY.md`](../../architecture/SETUPHELFER_PUBLIC_PRIVATE_STRATEGY.md)
- [`docs/faq/CLOUDSERVER_BOUNDARY_FAQ_DE.md`](../../faq/CLOUDSERVER_BOUNDARY_FAQ_DE.md)
