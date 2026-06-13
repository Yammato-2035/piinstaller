# APP Next Facade Candidates — Phase E.7 (EN)

**HEAD:** `72a7c93` · Assessment before further router slices (E.8+)

## Candidates

| Facade | Purpose | Affected routes | Risk | Rating | Recommendation |
|--------|---------|-------------------|------|--------|----------------|
| **DCC Status Facade** | Single entry for `build_dashboard_status`; profile gate | `GET /api/dev-dashboard/status`, indirectly roadmap/prompt-findings | CRITICAL | **CRITICAL** | **F.1 done** — F.2 router migration |
| **System Status Facade** | Traffic-light engine without route duplication | `GET /api/status`, `GET /api/system/status` | HIGH | **HIGH** | **G.1 done** — G.1b router migration |
| **Network Info Facade** | IP/hostname/interfaces | `GET /api/status`, `GET /api/system/network` | HIGH | **HIGH** | **G.2b done** — G.3 cleanup |
| **Settings Write Facade** | POST settings, UX, SMTP | `POST /api/settings*`, notifications/test | MEDIUM | **MEDIUM** | GET already E.2; write path separate |
| **Dev Dashboard Aggregation Facade** | control-center-summary, prompt-findings, cursor-meta-prompt | 3–4 GET | HIGH | **HIGH** | After DCC Status Facade |
| **Frontend Status ViewModel Facade** | Unified response shape for UI traffic lights | Frontend status consumers | MEDIUM | **MEDIUM** | **H.3 done** — H.4 rest |

## Priority

1. **CRITICAL:** DCC Status Facade
2. **HIGH:** Network Info (G.2b router migration)
3. **HIGH:** Dev Dashboard Aggregation
4. **MEDIUM:** Settings Write, Frontend ViewModel

## Module reuse

- No parallel lsblk/findmnt/subprocess in routers
- Register facades as **CANONICAL_MODULE** in `MODULE_CATALOG.md` before implementation
- Router slices delegate only to facade/core

## E.8 link

E.8 (3 notifications/backend-health GETs) does **not** require these facades — no `build_dashboard_status`.
