# DCC-VIS-001 Runtime Gate Status Model

## Achsen

1. **Local API** — `/health` + `/api/version` erreichbar
2. **Runtime Gate** — `check-runtime-deploy-gate.sh` / Phase 0
3. **Developer Token** — `X-Setuphelfer-Developer-Token`
4. **Aktionsmodus** — `read_only` | `developer_capable` | `blocked`
5. **Datenquelle** — `runtime_api` | `standalone_workspace` | `snapshot` | `unavailable`
6. **Operative Aktionen** — Deploy / Backup / Restore jeweils `erlaubt` | `gesperrt` (kein Fake-Green)

## Regel

`localApiReachable=true` + `apiReachable=false` → **nicht** „API OFFLINE“, sondern eingeschränkter Dev-Dashboard-Zugriff.

Implementierung: `frontend/src/dcc/visibility/runtimeStatusModel.ts`
