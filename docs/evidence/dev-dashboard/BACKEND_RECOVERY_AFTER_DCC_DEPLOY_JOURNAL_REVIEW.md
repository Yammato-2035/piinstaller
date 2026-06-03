# Backend Recovery — Journal Review

**Datum:** 2026-06-03

| Kriterium | Ergebnis |
|-----------|----------|
| Journal lesbar (Agent) | **no** (`-- No entries --`, Berechtigung) |
| Importfehler in Journal | **nicht belegt** |
| Port-Konflikt | **nicht belegt** |
| Operator-Terminal nach Deploy | `curl: (7) Failed to connect … 8000` + `daemon-reload` Warnung |

## Ursache (aus Deploy-Ablauf + Ist-Zustand)

1. `deploy-to-opt.sh` schrieb systemd-Unit-Dateien und startete Services **ohne** vorheriges `systemctl daemon-reload`.
2. Kurzzeitig: Backend nicht erreichbar auf `:8000`.
3. systemd meldete: Unit-Dateien geändert → **`daemon-reload` erforderlich**.
4. Nach Operator-Recovery (Reload/Restart): Backend **active**, API **200**, DCC-Route `recent-evidence` registriert.

**Status:** `daemon_reload_required` (Root Cause) — aktuell **recovered**
