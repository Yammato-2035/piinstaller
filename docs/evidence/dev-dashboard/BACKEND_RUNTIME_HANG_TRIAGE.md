# Backend Runtime Hang Triage

- Datum/Zeit (UTC): 2026-05-28T03:44:00Z
- Modus: STRICT MODE, read-only Triage
- Service: `setuphelfer-backend.service`

## 1) systemd / socket / Prozess

- `systemctl is-active` -> `active`
- `systemctl show`:
  - `ActiveState=active`, `SubState=running`
  - `MainPID=138932`
  - `ExecMainStartTimestamp=Wed 2026-05-27 22:41:20 CEST`
  - `MemoryCurrent=323084288`, `CPUUsageNSec=11503211392000`, `TasksCurrent=8`
  - `NRestarts=0`, `Restart=on-failure`
- `ss -ltnp '( sport = :8000 )'`:
  - LISTEN auf `127.0.0.1:8000`
  - `Recv-Q=2049`, `Send-Q=2048` (auffaellig: accept queue voll)
- `ps -p 138932 -o ...`:
  - Python/Uvicorn-Prozess laeuft, hoher CPU-Anteil (~37-38%), Zustand `Rsl`
- `ps -T -p 138932 -o ...`:
  - 8 Threads vorhanden; Hauptthread `Rsl`, weitere Threads `Ssl`

## 2) /proc-Inspektion (ohne sudo)

- `/proc/138932/status` lesbar:
  - `State: R (running)`, `Threads: 8`, `VmRSS: 280272 kB`
- `/proc/138932/stack`:
  - Nicht lesbar ohne erweiterte Rechte (`Keine Berechtigung`)
- `/proc/138932/fd`:
  - Nicht lesbar ohne erweiterte Rechte (`Keine Berechtigung`)
- `cwd`:
  - nicht aufloesbar im Agent-Kontext (Rechtegrenze)
- `cmdline`:
  - `/opt/setuphelfer/backend/venv/bin/python3 -m uvicorn app:app --host 127.0.0.1 --port 8000 --workers 1`

## 3) HTTP-Proben (time curl -v -m 3)

- `/api/version` -> TCP connected, dann Timeout (`curl_exit=28`, `time_real=3.00`)
- `/health` -> Connection timeout (`curl_exit=28`, `time_real=3.00`)
- `/docs` -> Connection timeout (`curl_exit=28`, `time_real=3.00`)
- `/openapi.json` -> TCP connected, dann Timeout (`curl_exit=28`, `time_real=3.00`)

## 4) Klassifikation

- Primaere Klasse: `backend_runtime_hang_accept_queue_saturation`
- Sekundaere Klassen:
  - `backend_api_hang_suspected`
  - `runtime_service_active_but_http_unresponsive`
  - `operator_privileged_diagnostics_required`

## 5) Bewertung und Folgeschritt

- Kein weiterer Restart-Versuch durch Agent (Policy eingehalten).
- Kein `sudo`, kein `kill`/`pkill`, keine Rescue-/Backup-/Restore-/Deploy-Aktion.
- Empfohlener naechster Prompt: `BACKEND_RUNTIME_OPERATOR_RESTART_RESULT_INGEST`.
- Voraussetzung: Operator fuehrt restart-/journal-Diagnostik in echtem Terminal aus und liefert Ergebnis-Evidence zur Rueckuebernahme.
