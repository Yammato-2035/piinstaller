# BACKEND_WATCHDOG_MVP_DECISION

**Stand:** 2026-05-28

## Entscheidung

| Variante | Rolle | Status |
|----------|-------|--------|
| **A** systemd `WatchdogSec` + `sd_notify` | Langfristig robust | Später (App-Heartbeat nötig) |
| **B** Healthcheck-Timer + oneshot Service | **MVP (Dateien)** | `packaging/systemd/*.example`, `scripts/healthcheck/setuphelfer-backend-healthcheck.sh` |
| **C** Tauri/Frontend Startup-Gate | UX + klare Fehler | `probeBackendStartup.ts`, Standalone-Banner |

**MVP:** B als **nicht aktivierte** Paket-Beispiele + C + Operator-Runbook. Kein automatischer Restart ohne `ENABLE_RESTART=1` und Operator-Freigabe.

## Warum `Restart=on-failure` nicht gegen Hänger hilft

Der Prozess bleibt ohne Exit-Code am Leben; systemd sieht **active**.

## Warum Port LISTEN kein Healthbeweis ist

TCP-Accept heißt nicht, dass der Worker HTTP bearbeiten kann (Event-Loop blockiert).

## Warum der Watchdog kein Rescue/Backup auslösen darf

Hang-Recovery ist **Infrastruktur**; Datenpfade bleiben hinter Phase-0-Gate und expliziter Freigabe.

## Warum der Timer nicht automatisch aktiv ist

Blinder Restart kann laufende Jobs beschädigen; Default `ENABLE_RESTART=0` nur loggen/melden.

## Operator

1. Gate lesen (Exit 17/18/14).
2. `journalctl -u setuphelfer-backend.service`
3. Restart nur mit Freigabe.
4. Gate erneut → Exit 0 vor Rescue.

JSON: `docs/evidence/dev-dashboard/backend_watchdog_mvp_decision_latest.json`
