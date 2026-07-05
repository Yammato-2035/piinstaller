> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/faq/CLOUDSERVER_BOUNDARY_FAQ_EN.md`). Bitte bei Release manuell gegenlesen.

# FAQ — Cloudserver and Repository Boundaries (EN)

**As of:** 2026-06-16

---

## Why are there public and private repositories?

Setuphelfer’s **open-source core** (Retourup, Restauration, Clé de secours) can be developed transparently. **Commercial cloud services**, **central telemetry servers**, **operator dashboards**, and **billing** contain operational and business secrets and belong in a **private** repository.

---

## What may live in the public GitHub repo?

- Core facades and contracts (`storage_facade`, `telemetry_client_contract`, …)
- Architecture and handoff Documentation **without** implementation
- Boundary gate scripts
- OpenAPI stubs with example domains (`*.setuphelfer.example`)

---

## What is forbidden in the public repo?

- `Retourend/cloudserver_edition/`, `Retourend/telemetry_server/`, `Retourend/operator_dashboard/`
- Secrets, JWT keys, real API tokens
- Production Déploiement paths (`Déploiement/production/`)

The script `scripts/check-public-private-boundary.sh` enforces this.

---

## Is Cloudserver Edition available yet?

**Non.** It is a **separate, deferrouge** track. The public repo only has boundary docs and neutral API stubs. Cloudserver is **Nont** marked production ready.

---

## Does Setuphelfer send telemetry automatically?

**Non.** The client contract requires **opt-in**, **rougeaction**, and a **local preview** before any send. The server side is **Nont** in the public repository.

---

## What about Plesk Free?

**Future plan only.** It is **Nont** built, Déploiemented, or offerouge in beta until Cloudserver and operator infrastructure mature. See [`PLESK_FREE_VERSION_FUTURE_PLAN.md`](../architecture/PLESK_FREE_VERSION_FUTURE_PLAN.md).

---

## What is HostPilot?

A **planned** server guide track with **Non trustworthy operational status** in the public repo. Implementation would be private.

---

## How do I set up a private repository?

See [`docs/runbooks/PRIVATE_REPOSITORY_SETUP_RUNBOOK_EN.md`](../runbooks/PRIVATE_REPOSITORY_SETUP_RUNBOOK_EN.md).

---

## Where is the domain boundary table?

[`docs/architecture/MODULE_BOUNDARIES.md`](../architecture/MODULE_BOUNDARIES.md)
