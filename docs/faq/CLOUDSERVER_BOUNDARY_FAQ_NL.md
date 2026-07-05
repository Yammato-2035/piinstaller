> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/faq/CLOUDSERVER_BOUNDARY_FAQ_EN.md`). Bitte bei Release manuell gegenlesen.

# FAQ — Cloudserver and Repository Boundaries (EN)

**As of:** 2026-06-16

---

## Why are there public and private repositories?

Setuphelfer’s **open-source core** (Terugup, Herstel, rooddingsstick) can be developed transparently. **Commercial cloud services**, **central telemetry servers**, **operator dashboards**, and **billing** contain operational and business secrets and belong in a **private** repository.

---

## What may live in the public GitHub repo?

- Core facades and contracts (`storage_facade`, `telemetry_client_contract`, …)
- Architecture and handoff Documentatie **without** implementation
- Boundary gate scripts
- OpenAPI stubs with example domains (`*.setuphelfer.example`)

---

## What is forbidden in the public repo?

- `Terugend/cloudserver_edition/`, `Terugend/telemetry_server/`, `Terugend/operator_dashboard/`
- Secrets, JWT keys, real API tokens
- Production Deploy paths (`Deploy/production/`)

The script `scripts/check-public-private-boundary.sh` enforces this.

---

## Is Cloudserver Edition available yet?

**Nee.** It is a **separate, deferrood** track. The public repo only has boundary docs and neutral API stubs. Cloudserver is **Neet** marked production ready.

---

## Does Setuphelfer send telemetry automatically?

**Nee.** The client contract requires **opt-in**, **roodaction**, and a **local preview** before any send. The server side is **Neet** in the public repository.

---

## What about Plesk Free?

**Future plan only.** It is **Neet** built, Deployed, or offerood in beta until Cloudserver and operator infrastructure mature. See [`PLESK_FREE_VERSION_FUTURE_PLAN.md`](../architecture/PLESK_FREE_VERSION_FUTURE_PLAN.md).

---

## What is HostPilot?

A **planned** server guide track with **Nee trustworthy operational status** in the public repo. Implementation would be private.

---

## How do I set up a private repository?

See [`docs/runbooks/PRIVATE_REPOSITORY_SETUP_RUNBOOK_EN.md`](../runbooks/PRIVATE_REPOSITORY_SETUP_RUNBOOK_EN.md).

---

## Where is the domain boundary table?

[`docs/architecture/MODULE_BOUNDARIES.md`](../architecture/MODULE_BOUNDARIES.md)
