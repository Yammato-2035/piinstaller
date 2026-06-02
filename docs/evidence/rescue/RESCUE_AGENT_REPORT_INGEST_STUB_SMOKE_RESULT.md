# Rescue-Agent Report-Ingest — Stub-Smoke Ergebnis

**Stand:** 2026-06-02  
**Status:** **blocked** (`rescue_agent_ingest_blocked_sudo_required`)

## Durchgeführt

| Phase | Ergebnis |
|-------|----------|
| 0 — Release-Block vor Ingest | **ok** — alle `/api/rescue-agent/*` → `PROFILE_ROUTE_BLOCKED` |
| 1 — OpenAPI/Contract read-only | **ok** — siehe `RESCUE_AGENT_INGEST_OPENAPI_CONTRACT_CHECK.md` |
| 2 — `local_lab` aktivieren | **blocked** — `sudo: Ein Passwort ist notwendig` |
| 3–7 — Live-Smoke | **not_run** |
| 8 — Release nach Smoke | **not_run** (Runtime blieb `release`) |

## Nicht behauptet

- Kein Live-Registration-Stub
- Kein Live-Report-Ingest
- Kein Fake-Green

## Contract (read-only belegt)

| Thema | Status |
|-------|--------|
| E2EE | `contract_stub_only` |
| nftables | `preview_only_apply_false` |
| Write/Apply-Routen | **none** unter `/api/rescue-agent` |

## Operator — Smoke fortsetzen

```bash
cd /home/volker/piinstaller

# local_lab
sudo install -m 0644 packaging/systemd/dropins/92-install-profile-local-lab.conf.example \
  /etc/systemd/system/setuphelfer-backend.service.d/install-profile.conf
sudo systemctl daemon-reload && sudo systemctl restart setuphelfer-backend.service

# Negative + Register + Report (siehe STRICT-MODE-Runbook)
# …

# release zurück
sudo install -m 0644 packaging/systemd/dropins/92-install-profile-release.conf.example \
  /etc/systemd/system/setuphelfer-backend.service.d/install-profile.conf
sudo systemctl daemon-reload && sudo systemctl restart setuphelfer-backend.service
```

## API-Body-Hinweis (Contract)

Live-API erwartet `SystemReportBody`: `session_id`, `agent_id`, optional `encrypted_envelope`, `test_mode_allow_unencrypted` — nicht das flache JSON aus älteren Runbook-Entwürfen.

## JSON

`rescue_agent_report_ingest_stub_smoke_latest.json`
