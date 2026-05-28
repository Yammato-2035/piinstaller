# BACKEND_WATCHDOG_AND_RECOVERY

## Fehlerarten

- **Startfehler:** Prozess startet nicht (systemd failed/inactive).
- **Crash:** Prozess beendet sich unerwartet (Restart-Policy kann greifen).
- **Hang:** Prozess lebt, Port offen, aber HTTP antwortet nicht.

## Warum `Restart=on-failure` nicht reicht

Ein Hang erzeugt oft keinen Exit-Code; der Prozess bleibt formal "running".

## Optionen

1. **systemd Watchdog (`WatchdogSec` + `sd_notify`)**
   - stark, aber App muss aktiv Watchdog-Heartbeat senden.
2. **Externer Healthcheck-Timer**
   - Timer/Service ruft `/health` auf und triggert bei Timeout einen kontrollierten Restart.
3. **Nur Runtime-Gate**
   - gut fuer Developer-Governance, ersetzt aber keinen System-Watchdog.

## Empfohlener MVP

- Kurzfristig: Runbook-basierter Operator-Flow fuer Hang.
- Mittelfristig: Healthcheck-Timer oder nativer systemd-Watchdog mit klarer Hang-Detektion.
- Keine automatische Deploy-/Recovery-Kette ohne explizite Freigabe.
