# FAQ — Cloudserver and Repository Boundaries (EN)

**As of:** 2026-06-16

---

## Why are there public and private repositories?

Setuphelfer’s **open-source core** (backup, restore, rescue stick) can be developed transparently. **Commercial cloud services**, **central telemetry servers**, **operator dashboards**, and **billing** contain operational and business secrets and belong in a **private** repository.

---

## What may live in the public GitHub repo?

- Core facades and contracts (`storage_facade`, `telemetry_client_contract`, …)
- Architecture and handoff documentation **without** implementation
- Boundary gate scripts
- OpenAPI stubs with example domains (`*.setuphelfer.example`)

---

## What is forbidden in the public repo?

- `backend/cloudserver_edition/`, `backend/telemetry_server/`, `backend/operator_dashboard/`
- Secrets, JWT keys, real API tokens
- Production deploy paths (`deploy/production/`)

The script `scripts/check-public-private-boundary.sh` enforces this.

---

## Is Cloudserver Edition available yet?

**No.** It is a **separate, deferred** track. The public repo only has boundary docs and neutral API stubs. Cloudserver is **not** marked production ready.

---

## Does Setuphelfer send telemetry automatically?

**No.** The client contract requires **opt-in**, **redaction**, and a **local preview** before any send. The server side is **not** in the public repository.

---

## What about Plesk Free?

**Future plan only.** It is **not** built, deployed, or offered in beta until Cloudserver and operator infrastructure mature. See [`PLESK_FREE_VERSION_FUTURE_PLAN.md`](../architecture/PLESK_FREE_VERSION_FUTURE_PLAN.md).

---

## What is HostPilot?

A **planned** server guide track with **no trustworthy operational status** in the public repo. Implementation would be private.

---

## How do I set up a private repository?

See [`docs/runbooks/PRIVATE_REPOSITORY_SETUP_RUNBOOK_EN.md`](../runbooks/PRIVATE_REPOSITORY_SETUP_RUNBOOK_EN.md).

---

## Where is the domain boundary table?

[`docs/architecture/MODULE_BOUNDARIES.md`](../architecture/MODULE_BOUNDARIES.md)
