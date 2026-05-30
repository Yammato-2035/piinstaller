# Control Center Overview Improvement — Evidence

**Date:** 2026-05-30
**Commit (feature):** 4b85bd2
**HEAD start (this run):** 4b85bd2
**HEAD end (this run):** (pending evidence commit)
**Branch:** main

## Runtime deploy acceptance (2026-05-30)

| Step | Result |
|------|--------|
| Deploy `./scripts/deploy-to-opt.sh` | **no** — `runtime_deploy_blocked_operator_sudo_required` |
| Backend restart | **no** (deploy blocked) |
| Web-UI restart | **no** (deploy blocked) |
| Runtime-Gate vor Deploy | Exit **14** (deploy drift — erwartet, Code noch nicht in `/opt`) |
| Runtime-Gate nach Deploy | **nicht geprüft** (Deploy blockiert) |

### Pre-deploy live checks

| Endpoint | Result |
|----------|--------|
| `/api/dev-dashboard/status` | OK |
| `/api/dev-server/health` | enabled=true, mode=local_lab, storage_ok=true, ssh_allowed=false, public_uploads_allowed=false |
| `/api/dev-server/summary` | node_count=2, reports_last_24h=2 |
| `/api/dev-dashboard/control-center-summary` | **HTTP 404** (alter Runtime-Stand) |

### Post-deploy live checks

**Nicht durchgeführt** — Operator muss Deploy mit sudo ausführen:

```bash
sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller
sudo systemctl restart setuphelfer-backend.service
sudo systemctl restart setuphelfer.service
./scripts/check-runtime-deploy-gate.sh
curl -s http://127.0.0.1:8000/api/dev-dashboard/control-center-summary | jq .
```

## Workspace / unit tests (pre-deploy)

| Check | Result |
|-------|--------|
| Aggregator (Python lokal) | OK — 13 Roadmap-Areas, 1173 Docs |
| Backend tests `test_dev_control_center_*` | 9 OK |
| Frontend tests ControlCenterOverview | 4 OK |

## Feature status

| Feature | Code | Runtime live |
|---------|------|--------------|
| Control Center Overview UI | GREEN | **pending** (Deploy) |
| Summary API | GREEN (code) | **404 / blocked** |
| Roadmap tab | GREEN (code) | pending |
| Telemetry card | GREEN (code) | pending |
| Doc/Diagnostics stats | GREEN (code) | pending |
| Frontend HTTP smoke | — | **pending** |

## Frontend runtime smoke

**pending** — Web-UI nicht nach Deploy geprüft (Deploy blockiert).

## Safety

- Kein ISO-Build, USB-Write, Backup, Restore, SSH, apt
- Public uploads disabled (live weiterhin korrekt)
- SSH disabled (live weiterhin korrekt)
- Keine Fake-Greens für Summary-Endpoint

## Operator next steps

1. Deploy + Restart (siehe Befehle oben)
2. Summary-Endpoint auf HTTP 200 prüfen
3. Control Center im Browser öffnen (Tab Überblick / Telemetrie)
4. Evidence-Commit nach erfolgreichem Smoke ergänzen oder erneuten Acceptance-Lauf starten

## Open points

- Runtime deploy mit sudo (Operator)
- Frontend Live-Ansicht manuell prüfen
- Roadmap-Datenqualität
- Documentation-Coverage-Metriken
- SSE/WebSocket Live-Refresh
- Rescue ISO Dry-Build (pending)

## Next prompt

Nach erfolgreichem Deploy + Summary HTTP 200:

**RESCUE DEVELOPER ISO DRY-BUILD WITH DEV AGENT PROFILE GUARD**

Bei weiterem 404 nach Deploy:

**FIX CONTROL CENTER SUMMARY ROUTE / DEPLOY DRIFT**
