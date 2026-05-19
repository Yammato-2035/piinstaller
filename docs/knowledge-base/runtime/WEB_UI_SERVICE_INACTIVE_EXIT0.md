# KB: Web-UI-Dienst inactive mit Exit 0

| Feld | Inhalt |
|------|--------|
| **Symptom** | `setuphelfer.service` **inactive (dead)**; `curl http://127.0.0.1:3001` → connection refused; systemd: `code=exited, status=0/SUCCESS` |
| **Komponente** | `setuphelfer.service` → `scripts/start-browser-production.sh` |
| **Backend oft OK** | `curl http://127.0.0.1:8000/api/version` kann trotzdem funktionieren |

## Root cause

Unter **`Type=simple`** war die **Bash-Shell** der Hauptprozess. Das Skript startete **`npm run preview &`** und **`wait`**. Wenn der Hintergrundprozess endete oder Signale ankamen (`trap cleanup`), beendete sich die Shell mit **Exit 0** — systemd markierte die Unit als **dead**, ohne Listener auf **3001**.

## Fix (ab Commit `0a1e4a0`)

```bash
exec npm run preview -- --host 127.0.0.1 --port 3001 --strictPort
```

- Vite bleibt Hauptprozess (PID für systemd) — **nur bei älteren Deployments**, die noch Vite-Preview nutzen  
- Kein `npm install` / `npm run build` im Service-Start  
- Fehlendes `dist/index.html` → Exit **1** mit klarer Meldung  

## Follow-up: statischer Python-Server (aktuell)

Für neue Deployments liefert **`scripts/serve-frontend-production.py`** die SPA aus **`frontend/dist/`** ohne Node zur Laufzeit. Details: `docs/operations/WEB_UI_RUNTIME_SERVICE_DE.md`, Evidence `docs/evidence/runtime-results/web_ui_reload_crash_repair_2026-05-19.json`.

## Prüfkommandos

```bash
systemctl is-active setuphelfer.service
ss -ltnp | grep ':3001'
curl -I http://127.0.0.1:3001
```

Erwartung nach Fix: **active**, Port **3001** LISTEN, **HTTP 200**.

## Abgrenzung

| Situation | Hinweis |
|-----------|---------|
| Backend down, UI up | Nur `:8000` prüfen / `setuphelfer-backend.service` |
| UI zeigt „Backend nicht erreichbar“, Port 3001 OK | API-Basis in Release: `http://127.0.0.1:8000` (nicht Same-Origin auf :3001) — siehe Commit `416223b` |
| SMTP-Testmail fehlgeschlagen | Separates Thema (`smtp_auth_failed` etc.), kein UI-Service-Exit-0 |

## Evidence

`docs/evidence/runtime-results/setuphelfer_web_ui_runtime_repair_2026-05-18.json`  
`docs/evidence/runtime-results/web_ui_reload_crash_repair_2026-05-19.json`

## Ausführliche Doku

- `docs/operations/WEB_UI_RUNTIME_SERVICE_DE.md`
- `docs/operations/WEB_UI_RUNTIME_SERVICE_EN.md`
