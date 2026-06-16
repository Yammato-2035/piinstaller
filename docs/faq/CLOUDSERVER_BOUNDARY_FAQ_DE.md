# FAQ — Cloudserver- und Repository-Grenzen (DE)

**Stand:** 2026-06-16

---

## Warum gibt es ein öffentliches und ein privates Repository?

Setuphelfer ist als **Open-Source-Kern** (Backup, Restore, Rettungsstick) transparent entwickelbar. **Kommerzielle Cloud-Dienste**, **zentrale Telemetrie-Server**, **Operator-Dashboards** und **Billing** enthalten Betriebs- und Geschäftsgeheimnisse und gehören in ein **privates** Repository.

---

## Was darf im öffentlichen GitHub-Repo stehen?

- Core-Facades und Contracts (`storage_facade`, `telemetry_client_contract`, …)
- Architektur- und Handoff-Dokumentation **ohne** Implementierung
- Boundary-Gate-Skripte
- OpenAPI-Stubs mit Beispiel-Domains (`*.setuphelfer.example`)

---

## Was ist verboten im Public-Repo?

- `backend/cloudserver_edition/`, `backend/telemetry_server/`, `backend/operator_dashboard/`
- Secrets, JWT-Keys, echte API-Tokens
- Produktions-Deploy-Pfade (`deploy/production/`)

Das Skript `scripts/check-public-private-boundary.sh` prüft das automatisch.

---

## Ist die Cloudserver Edition schon verfügbar?

**Nein.** Sie ist ein **separater, zurückgestellter** Track. Im Public-Repo gibt es nur Grenzdoku und neutrale API-Stubs. Kein „grün“ oder „production ready“ für Cloudserver.

---

## Sendet Setuphelfer automatisch Telemetrie?

**Nein.** Der Client-Contract verlangt **Opt-in**, **Redaction** und **lokale Vorschau** vor einem Send. Der Server-Teil ist **nicht** im öffentlichen Repository.

---

## Was ist mit Plesk Free?

**Zukunftsplan nur.** Es wird **nicht** gebaut, deployed oder im Beta-Scope angeboten, bis Cloudserver und Operator-Infrastruktur reif sind. Siehe [`PLESK_FREE_VERSION_FUTURE_PLAN.md`](../architecture/PLESK_FREE_VERSION_FUTURE_PLAN.md).

---

## Was ist HostPilot?

Ein **geplanter** Serverguide-Track **ohne** belastbare operative Statusquelle im Public-Repo. Implementierung wäre privat.

---

## Wie starte ich ein privates Repository?

Siehe [`docs/runbooks/PRIVATE_REPOSITORY_SETUP_RUNBOOK_DE.md`](../runbooks/PRIVATE_REPOSITORY_SETUP_RUNBOOK_DE.md).

---

## Wo finde ich die Domänentabelle?

[`docs/architecture/MODULE_BOUNDARIES.md`](../architecture/MODULE_BOUNDARIES.md)
