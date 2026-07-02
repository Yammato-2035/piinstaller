# Setuphelfer Private — Monorepo Skeleton

Copy this tree into a **private** GitHub repository (e.g. `Yammato-2035/setuphelfer-private`).
Do **not** fork `piinstaller`. Use `scripts/bootstrap-setuphelfer-private-repo.sh` from the public repo.

## Layout

| Path | Port (lab) | Role |
|------|------------|------|
| `beta-registration-server/` | 8100 / 8200 prod | Accounts, sticks, agreements |
| `telemetry-server/` | 8101 | Ingest, quarantine, no remote commands |
| `diagnostics-server/` | 8102 | Hardware DB, learning import |
| `operator-dashboard/` | — | Placeholder |
| `infra/` | — | docker-compose lab stack |
| `public-contracts/` | — | Git submodule → piinstaller |

## Quick start (lab)

```bash
./scripts/start-rescue-lab-mocks.sh          # from public piinstaller repo
# or after private repo bootstrap:
docker compose -f infra/docker-compose.lab.yml up
```

## Boundary

Public `piinstaller` = contracts only. This tree = server implementation. No secrets in git.

See `docs/architecture/PUBLIC_PRIVATE_BOUNDARY_V1.md` in public-contracts submodule.
