# BACKEND_CURRENT_AVAILABILITY_AUDIT

## Scope

- Read-only availability check.
- No `sudo`, no restart, no deploy, no process kill.

## Commands and outcomes

- `./scripts/check-runtime-deploy-gate.sh || true`
  - `check-runtime-deploy-gate: /api/version HTTP 000000`
- `systemctl is-active setuphelfer-backend.service || true`
  - `active`
- `systemctl status setuphelfer-backend.service --no-pager || true`
  - service running, uvicorn on `127.0.0.1:8000`
- `ss -ltnp | grep ':8000' || true`
  - port `8000` listening
- `curl -sS -m 5 http://127.0.0.1:8000/api/version || true`
  - timeout
- `curl -sS -m 5 http://127.0.0.1:8000/health || true`
  - timeout
- `curl -sS -m 5 http://127.0.0.1:8000/api/dev-dashboard/status || true`
  - timeout
- `curl -sS -m 5 http://127.0.0.1:8000/api/dev-dashboard/roadmap || true`
  - timeout

## Classification

- `backend_hanging`

## Interpretation

- Process and socket are present.
- API does not return within 5s across all tested endpoints.
- Runtime-gate remains blocked due to HTTP 000000 behavior.
