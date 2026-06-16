# Runbook — Private Repository Setup (EN)

**As of:** 2026-06-16  
**Audience:** Maintainers with access to public and private repositories  
**Status:** Process documentation — not an automated deploy

---

## 1. Purpose

Step-by-step guide to create and maintain a **private Setuphelfer repository** for Cloudserver Edition, telemetry server, diagnostics server, operator dashboard, and commercial modules — separate from the **public** `piinstaller` repository.

---

## 2. Prerequisites

| # | Requirement |
|---|-------------|
| 1 | Git hosting with **private** visibility |
| 2 | Maintainer role on the public repo |
| 3 | Secret manager or CI vault (no secrets in git) |
| 4 | Familiarity with public boundary gates |
| 5 | Legal sign-off for beta/production (see `docs/legal/`) |

---

## 3. Decision tree: public vs. private

```text
New feature?
    │
    ├─ Facade / contract / OSS docs? ──► Public repo
    │
    ├─ Server ingest / billing / operator UI? ──► Private repo
    │
    └─ Unclear? ──► STOP · architecture review · handoff doc
```

---

## 4. Create private repository

### 4.1 Repository

1. Create a new repo with **private** visibility (e.g. `setuphelfer-private`).
2. Protect default branch `main` (PR required, status checks).
3. Do **not** mirror the entire public tree — selective integration only.

### 4.2 Base layout

```text
setuphelfer-private/
  README.md
  backend/
    cloudserver_edition/
    telemetry_server/
    diagnostics_server/
    operator_dashboard/
  commercial/
  infra/staging/
  docs/handoff/
  scripts/check-private-import-boundaries.sh
```

### 4.3 Public dependency (pick one)

| Option | Pros | Cons |
|--------|------|------|
| **Git submodule** | Exact commit pinning | Submodule overhead |
| **Package (wheel/npm)** | Clean versioning | Release pipeline needed |
| **Vendor copy** | Simple | Drift risk |

Recommendation: submodule pinned to public release tags for contract files.

---

## 5. Boundary gates

### 5.1 Public repo (before every push)

```bash
./scripts/check-public-private-boundary.sh
./scripts/check-module-boundaries.sh
```

Expect no exit 10–16 (blocked). Exit 20 = manual review.

### 5.2 Private repo

- CI: verify import direction (private may import public, never reverse)
- Secret scan on commits
- Never push private artifacts to the public remote

---

## 6. Secrets and configuration

| Secret type | Storage | Forbidden |
|-------------|---------|-----------|
| Telemetry signing key | CI vault | Git |
| JWT / session secret | Operator infra | Public repo |
| SMTP / billing API | Secret manager | `.env` in repo |
| Plesk/API tokens (future) | Private CI only | Real values in public docs |

Documentation placeholder domains: `*.setuphelfer.example`

---

## 7. Handoff checklist (per module)

| Module | Handoff document | Owner sign-off |
|--------|------------------|----------------|
| Cloudserver | `docs/private-handoff/CLOUDSERVER_PRIVATE_REPO_HANDOFF.md` | [ ] |
| Telemetry server | `TELEMETRY_INTERNAL_SERVER_HANDOFF.md` | [ ] |
| Diagnostics server | `DIAGNOSTICS_INTERNAL_SERVER_HANDOFF.md` | [ ] |
| Operator dashboard | `OPERATOR_DASHBOARD_PRIVATE_HANDOFF.md` | [ ] |
| Plesk Free (later) | `PLESK_FREE_VERSION_FUTURE_HANDOFF.md` | [ ] |

---

## 8. CI/CD (minimum)

1. Lint + unit tests on private code
2. Contract tests against public `*_contract.py` / OpenAPI
3. Boundary gates on both repos
4. Staging deploy only from private pipeline
5. No auto-deploy to production without runbook approval

---

## 9. Sync public → private

When contracts change in the public repo:

1. Check `CONTRACT_VERSION` / OpenAPI `version`
2. Bump submodule or package
3. Run private integration tests
4. Update handoff docs on breaking changes

---

## 10. Incident and rollback

| Scenario | Action |
|----------|--------|
| Secret leaked in public repo | Rotate keys, scrub history (owner), extend gate |
| Private code in public PR | Close PR, review boundary gate |
| Contract drift | Block private build until synced |

---

## 11. Beta and legal gates

Before external beta:

- [`docs/legal/BETA_TEST_READINESS_CHECKLIST_EN.md`](../legal/BETA_TEST_READINESS_CHECKLIST_EN.md)
- German NDA/beta items: `NDA_REQUIRED_ITEMS_DE.md`, `BETA_AGREEMENT_REQUIRED_ITEMS_DE.md`

---

## 12. Private repo setup sign-off

- [ ] Private visibility verified
- [ ] Authorized collaborators only
- [ ] Boundary gates in CI
- [ ] Secrets outside git
- [ ] Handoff docs assigned
- [ ] No production testing against `/opt` without Phase 0 runtime gate

---

## 13. References

- [`PUBLIC_PRIVATE_MODULE_BOUNDARIES.md`](../architecture/PUBLIC_PRIVATE_MODULE_BOUNDARIES.md)
- [`SETUPHELFER_PUBLIC_PRIVATE_STRATEGY.md`](../architecture/SETUPHELFER_PUBLIC_PRIVATE_STRATEGY.md)
- [`PUBLIC_PRIVATE_BOUNDARY_RULES.md`](../evidence/public-private/PUBLIC_PRIVATE_BOUNDARY_RULES.md)
