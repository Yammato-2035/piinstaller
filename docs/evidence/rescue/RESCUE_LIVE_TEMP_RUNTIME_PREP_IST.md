# Rescue Live Temp Runtime — IST-Stand (Prep)

**Datum:** 2026-05-24  
**Git HEAD:** `6adfcf6`  
**Zweck:** Vorbereitung Live-Medium-Test mit temporärer Setuphelfer-Runtime (read-only, local-only)

## Was ist bereits vorhanden?

| Bereich | Status | Pfad / Hinweis |
|---------|--------|----------------|
| Build-Emulation Final-Gate | **ready** | `rescue_stick_readonly_build_final_gate.json`, `live_os_network_test_pending: true` |
| Live-OS Validation Plan/Runbook | vorhanden | `RESCUE_STICK_LIVE_OS_NETWORK_VALIDATION_PLAN.md`, `RESCUE_STICK_LIVE_OS_NETWORK_VALIDATION_RUNBOOK.md` |
| Live-OS Result (Host-Proxy) | **review_required** | `RESCUE_STICK_LIVE_OS_NETWORK_VALIDATION_RESULT.md` — kein gebootetes Live-Medium |
| Runtime unter `/opt` | aktiv | Backend `127.0.0.1:8000`, UI `127.0.0.1:3001`, CDN-frei |
| Deploy-Runner Emulation | vorhanden | `backend/deploy/runner_rescue_stick_readonly_build_emulation.py` |
| Frontend dist | vorhanden | `frontend/dist/` (nach `npm run build`) |
| Backend + venv (Deploy) | vorhanden | `backend/`, `backend/venv/` nach `deploy-to-opt.sh` |
| UI-Server (stdlib) | vorhanden | `scripts/serve-frontend-production.py` |
| Version | vorhanden | `config/version.json`, `VERSION` |
| VM/Live-Hilfen (Referenz) | vorhanden | `tools/vm-test/scripts/` (nicht für diesen Auftrag ausführen) |

## Was fehlt für echten Live-Medium-Test?

1. **Gebootetes** Debian-/Ubuntu-Live-System (freigegebenes Testmedium, kein ISO-Build hier).
2. **Temp-Bundle** auf Live-Medium kopiert/entpackt (Operator, ohne mount/dd in diesem Prep-Auftrag).
3. **systemd-networkd** als Netzwerk-Stack auf Live-Medium validiert (nicht Host NetworkManager).
4. **Offline-Test** ohne WAN auf Live-Medium.
5. **Evidence** aus Live-Session in Result-Datei (Template vorbereitet).

## Erlaubte Dateien im temporären Bundle

| Pfad | Rolle |
|------|--------|
| `backend/` (ohne `__pycache__`, mit gebündelter `venv/`) | API localhost |
| `frontend/dist/` | Statische UI |
| `scripts/rescue-live/` | Local-only Start + Check |
| `scripts/serve-frontend-production.py` | UI-Server |
| `config/version.json` | Version |
| `VERSION` | Kurzversion |
| `README_RESCUE_TEMP_RUNTIME.md` | Operator-Hinweise (im Bundle) |

## Verbotene Dateien / Muster

- `.env`, Secrets, Tokens, Credentials
- `node_modules/`, Dev-`venv` ohne Deploy-Seal
- Backups, Restore-Artefakte (`*.tar.gz`, `*.backup`, `*.restore`)
- ISO/IMG/QCOW2, `build/rescue/emulation/*.json` (regenerierbar)
- Private Host-Pfade (`/home/*`, `/media/*` in Config)
- Automatische Write-/Restore-/Partition-Skripte beim Start

## Sichere Startbefehle (local-only)

```bash
export SETUPHELFER_RESCUE_ROOT=/path/to/setuphelfer-rescue-runtime
./scripts/rescue-live/start-backend-localonly.sh   # Terminal 1
./scripts/rescue-live/start-ui-localonly.sh        # Terminal 2
./scripts/rescue-live/check-localonly.sh           # Prüfung
```

**Erzwungen:** `127.0.0.1` für Backend und UI; `ALLOW_REMOTE_ACCESS` blockiert im Backend-Skript.

## Blocked / review_required

| Punkt | Status |
|-------|--------|
| ISO-Build | **blocked** |
| apt/chroot/mount auf Live-Medium (in Prep) | **blocked** |
| `real_iso_build_allowed` | **false** |
| Live-OS Network Validation gesamt | **review_required** bis Hardware-Live-Test |
| Temp Runtime Prep (Skripte + Doku) | **green** nach Commit dieser Prep-Dateien |

## Referenzen

- `RESCUE_TEMP_RUNTIME_BUNDLE_PREVIEW.md`
- `docs/runbooks/RESCUE_STICK_TEMP_RUNTIME_ON_LIVE_MEDIUM_RUNBOOK.md`
- `RESCUE_STICK_LIVE_OS_NETWORK_VALIDATION_RESULT_TEMPLATE.md`
