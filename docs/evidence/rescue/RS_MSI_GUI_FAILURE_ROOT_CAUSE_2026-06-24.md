# RS-001 MSI GUI Failure — Root Cause (2026-06-24)

## Symptom (Operator)

- MSI GE63 bootet in **Textmodus**
- Grafische Oberfläche startet nicht automatisch
- Vermutung: `setuphelfer-backend.service` Restart-Loop

## Evidence-Quelle

Harvested von **SETUP_LOGS** nach MSI-Boot (`/media/volker/SETUP_LOGS/setuphelfer/evidence/gui-failure/`).

## Phase 0 — Live Evidence (Stick)

| Artefakt | Pfad |
|----------|------|
| gui-watchdog | `evidence/boot/gui-watchdog.json` |
| rescue-ui-status | `evidence/boot/rescue-ui-status.json` |
| gui-start.log | `logs/boot/gui-start.log` (BOOT_ID `5f4e2a45`, 2026-06-24T23:47Z) |
| service-status | `diagnostics/latest/54-service-status.txt` (Boot 22:47Z) |
| Root-cause JSON | `evidence/gui-failure/ROOT_CAUSE_ANALYSIS.json` |

## Phase 1 — Restart-Loop (Backend)

| Feld | Wert (Evidence) |
|------|-----------------|
| 23:47 Boot | GUI scheitert **vor** Backend-Health-Loop |
| 22:47 Boot | `setuphelfer-backend.service` **active (running)**, PID 1764, kein Restart-Counter in Journal |
| systemd failed units | **0** (`51-systemd-failed.txt`) |

**Fazit:** Restart-Loop in geernteten Logs **nicht belegt**. Primärfehler ist GUI-Watchdog `chromium_missing`, nicht Backend-Crash.

## Phase 2 — GUI-Watchdog Entscheidung (23:47 Boot)

```
[CHECK_FRONTEND] ok=/usr/share/setuphelfer/rescue/ui/rescue.html
[BACKEND_START] async_pid=1843
[CHECK_BROWSER] RESULT=missing
[GUI_WATCHDOG_STATE] gui_started=false gui_failed=true code=chromium_missing
```

`gui-watchdog.json`:

```json
{
  "gui_error_code": "chromium_missing",
  "fallback_to_tui": true
}
```

## Phase 3 — Root Cause (belegt)

| SquashFS | SHA256 (short) | Größe | `usr/bin/chromium` |
|----------|----------------|-------|---------------------|
| **1.9.16.3** (auf Stick) | `3bc45589…` | 534M | **NEIN** |
| **1.9.16.2** | `fc8cac9d…` | 1.2G | **JA** |
| Repack-Quelle 1.7.10.0 | `a54aae1d…` | 531M | **NEIN** |

**Ursache:** Payload `1.9.16.3` wurde per `repack-rescue-squashfs-react-shell.sh` von **`filesystem.squashfs.repacked-1.7.10.0`** (Default) repacked — **ohne Chromium-Paket**. Watchdog prüft `command -v chromium` → fehlt → `fallback_to_tui`.

**Watchdog-Klasse:** Nicht A (Backend), nicht C (Crash) — **fehlendes Payload-Artefakt** vor GUI-Start.

## Phase 4 — Vergleich erfolgreicher Boot (22:47)

- SquashFS auf Medium: `fc8cac9d…` (1.9.16.2)
- Chromium läuft: `/usr/lib/chromium/chromium … --kiosk`
- `gui-watchdog.json`: `gui_started=true`
- `rescue-ui-status.json`: `status=ready`, `menu_visible=true`

## Phase 5 — Fix (Code, nicht deployed)

1. `repack-rescue-squashfs-react-shell.sh`: Source-Default → neuester SquashFS **mit** `usr/bin/chromium` (bevorzugt `1.9.16.2`)
2. `rescue_squashfs_react_shell_verify.py`: Check `chromium_browser` Pflicht
3. Repack schlägt fehl wenn Output kein Chromium enthält

**Operator-Aktion (separate Freigabe):** Repack von `1.9.16.2`-Basis → neues 1.9.16.3+ Payload → Stick-Update. **Nicht in dieser Session** (Kein Rebuild/Kein USB-Write).

## Phase 6–9 — MSI Retest

**AUSSTEHEND** nach korrigiertem Payload.

## Gesamtstatus

| Bereich | Status |
|---------|--------|
| Root Cause identifiziert | **GRÜN** (belegt) |
| GUI auf MSI mit 1.9.16.3 | **ROT** |
| Backend Restart-Loop | **UNBESTÄTIGT** (nicht in Evidence) |
| Fix deployed | **ROT** (nur Code-Vorbereitung) |

**Gesamt: ROT** — GUI startet mit aktuellem Stick-Payload 1.9.16.3 nicht.
