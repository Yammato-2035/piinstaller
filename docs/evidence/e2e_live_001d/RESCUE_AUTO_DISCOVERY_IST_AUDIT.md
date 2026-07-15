# Rescue Auto-Discovery IST-Audit (001D7)

## State-Quellen (vor 001D7)

| Quelle | Pfad | Schreiber | Leser |
|--------|------|-----------|-------|
| Auto-E2E State | `/run/setuphelfer-rescue/auto-e2e/state.json` | Orchestrator, auto-msi-evidence | TUI, Failsafe |
| Session Pointer | `/run/setuphelfer/current-session.json` | boot-init | Collector, Eval |
| Run-Control | `SETUP_LOGS/.../run-control.json` | Dev-Skript | Physical E2E |
| MSI complete | `.../msi-evidence-complete.json` | auto-msi-evidence | Physical E2E, TUI |
| Lab result | `.../lab-auto-result.json` | Eval | Reporting |

## Race Conditions (belegt 1.10.0.24)

1. TUI-Phase aus Uptime statt Service-Status → 30 min Schein-Collect
2. `auto-msi-evidence` hing an `start-assistant` (inaktiv im Lab)
3. `lab-auto-result passed` ohne `msi-evidence-complete.json`
4. Fehlende Backend-Module im SquashFS (`ensure_setup_logs_rw`, Bundle)
5. boot-progress kann TTY1 schreiben trotz Shield

## 001D7 Änderungen

- Primäre Wahrheit: `/run/setuphelfer-rescue/session/state.json`
- Persistenz: `SETUP_LOGS/setuphelfer/evidence/sessions/<SESSION_ID>/`
- Neuer Dienst: `setuphelfer-rescue-auto-discovery.service` (read-only)
- TTY-Gate: `scripts/check-rescue-exclusive-tty-owner.sh`
- `start-assistant` aus auto-msi-evidence entfernt
- TUI liest Session-State mit Live-Refresh

## Marker-Kette Physical E2E (unverändert, nach Discovery)

```text
msi-evidence-complete.json → auto-physical-e2e → run-control consumed
```

001D7 aktiviert **keine** destruktiven Storage-Aktionen.
