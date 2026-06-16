# Public/Private Modulgrenzen

**Stand:** 2026-06-16  
**Gate:** `scripts/check-public-private-boundary.sh`, `scripts/check-private-import-boundaries.sh`  
**Status:** Aktiv — Public-Repository ist **öffentlich**; private Implementierung gehört in ein separates Repository.

---

## Grundregel

```
┌─────────────────────────────────────────────────────────┐
│  PUBLIC REPO (GitHub, open source)                       │
│  • Facades, Contracts, Stubs, Doku, Handoff            │
│  • Darf NIEMALS private Module importieren             │
└───────────────────────┬─────────────────────────────────┘
                        │  Contracts only (one-way)
                        ▼
┌─────────────────────────────────────────────────────────┐
│  PRIVATE REPO (proprietary)                              │
│  • Cloudserver Edition, Telemetry Server, Diagnostics    │
│  • Operator Dashboard, License/Billing                   │
│  • Darf public Contracts importieren/spiegeln            │
└─────────────────────────────────────────────────────────┘
```

---

## Import-Matrix

| Von → Nach | Public Module | Private Module |
|------------|---------------|----------------|
| **Public** | ✅ Erlaubt (innerhalb Regeln) | ❌ **Verboten** |
| **Private** | ✅ Contracts/Facades (read-only Spiegel oder Git-Submodule) | ✅ Erlaubt |
| **CI/Gate** | Prüft verbotene Pfade und Begriffe | Separates Gate im Private-Repo |

---

## Was bleibt public

- `backend/core/*_facade.py`, `*_contract.py` (ohne Server-Interna)
- Rescue-/Deploy-Contracts und plan-only APIs
- `docs/architecture/*`, `docs/api/*`, `docs/knowledge-base/cloud/*`
- `docs/private-handoff/*` — **Handoff-Beschreibungen**, keine Implementierung
- Boundary-Gate-Skripte und zugehörige Tests

---

## Was ist private-only

| Bereich | Typischer Pfad (nur im Private-Repo) |
|---------|--------------------------------------|
| Cloudserver Edition | `backend/cloudserver_edition/`, `backend/cloudserver_private/` |
| Telemetrie-Server | `backend/telemetry_server/`, `backend/internal_telemetry/` |
| Diagnostikserver (intern) | `backend/diagnostics_server/`, `backend/internal_diagnostics/` |
| Operator Dashboard | `backend/operator_dashboard/`, `frontend/src/operator/` |
| Lizenz / Billing / Abo | `licensing/`, `billing/`, `subscriptions/`, `commercial/` |
| Produktions-Infra | `deploy/production/`, `infra/production/` |

Details: [`docs/evidence/public-private/PUBLIC_PRIVATE_BOUNDARY_RULES.md`](../evidence/public-private/PUBLIC_PRIVATE_BOUNDARY_RULES.md)

---

## Plesk Free — nur Zukunft

**Plesk Free** ist ein **geplanter**, noch **nicht implementierter** Track:

- Kein Build, kein Live-Deploy, kein Katalog-Submit aus dem Public-Repo
- Public-Repo enthält nur Planungsdoku: [`PLESK_FREE_VERSION_FUTURE_PLAN.md`](PLESK_FREE_VERSION_FUTURE_PLAN.md)
- Implementierung und Secrets ausschließlich im Private-Repo (wenn freigegeben)

---

## Erlaubte Platzhalter-Domains (Doku/Tests)

- `telemetry.internal.setuphelfer.example`
- `operator.internal.setuphelfer.example`
- `diagnose.internal.setuphelfer.example`
- `cloud.private.setuphelfer.example`
- `api.internal.setuphelfer.example`

Echte Produktions-Domains, Tokens und SMTP-Zugangsdaten **dürfen nicht** in Commits erscheinen.

---

## Verbotene Begriffe in Public-Commits (Auszug)

`TELEMETRY_SERVER_SECRET`, `LICENSE_ENFORCEMENT`, `OPERATOR_DASHBOARD` (als Implementierungsmarker), `PLESK_CATALOG_SUBMISSION_SECRET`, `JWT_SECRET`, … — vollständige Liste im Gate-Skript.

---

## Konsequenz für Entwickler

1. Neue Features zuerst als **Contract** oder **Facade** im Public-Repo definieren.  
2. Server-/Operator-Logik im Private-Repo implementieren und gegen Contracts testen.  
3. Vor jedem Push: `./scripts/check-public-private-boundary.sh`  
4. Bei `exit 20` (`review_required`): manuelle Prüfung, kein Workaround durch Umbenennung sensibler Logik.

---

## Verwandte Dokumente

- [`SETUPHELFER_PUBLIC_PRIVATE_STRATEGY.md`](SETUPHELFER_PUBLIC_PRIVATE_STRATEGY.md)  
- [`CLOUDSERVER_EDITION_PRIVATE_BOUNDARY.md`](CLOUDSERVER_EDITION_PRIVATE_BOUNDARY.md)  
- [`docs/runbooks/PRIVATE_REPOSITORY_SETUP_RUNBOOK_DE.md`](../runbooks/PRIVATE_REPOSITORY_SETUP_RUNBOOK_DE.md)
