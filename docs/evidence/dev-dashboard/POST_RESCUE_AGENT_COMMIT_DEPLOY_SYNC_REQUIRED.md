# Post Rescue-Agent-Commit — Operator Deploy-Sync erforderlich

**Stand:** 2026-06-02  
**HEAD nach Rescue-Agent-Commit:** `2e602d0`

## Warum jetzt Deploy?

Nach Commit `00615d5` + Rescue-Agent-Commit fehlen in `/opt/setuphelfer` u. a.:

- `backend/rescue_agent/` (gesamtes Paket)
- Fleet-Heartbeat-Änderungen in `fleet_session_state.py`
- `install_profile.py` (`/api/rescue-agent` Forbidden + Router-Registrierung)
- App-Bootstrap aus `00615d5` (falls noch nicht deployed)

**Restart ohne Deploy reicht nicht** — Uvicorn lädt Code aus `/opt`, nicht aus dem Workspace.

## Operator-Aktion (nur nach Freigabe)

```bash
sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller
sudo systemctl restart setuphelfer-backend.service
./scripts/check-runtime-deploy-gate.sh
./scripts/check-runtime-profile-deploy-gate.sh
```

## Vor Deploy grün (Workspace)

- Import + py_compile OK
- 32+ Rescue/Fleet pytest OK
- Frontend build + 54 Vitest OK

## Live-Smokes nach Deploy (nicht in diesem Lauf)

1. `local_lab` Profil setzen (Operator)
2. Fleet: Create → Heartbeat (`agent_state=alive`) → Finish
3. `GET /api/rescue-agent/sessions` (lab)
4. DCC: Rescue-Agent-Panel, kein Crash bei 404 in release
5. Controlled ISO precheck (kein Build ohne Freigabe)

## Keine Aktion in diesem Dokument-Lauf

- Kein Deploy, kein Restart ausgeführt
