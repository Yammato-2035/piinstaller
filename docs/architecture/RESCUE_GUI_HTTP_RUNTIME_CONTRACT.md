# Rescue GUI HTTP Runtime Contract (PI-RS-BVR-GUI-DCC-001)

**Task:** PI-RS-BVR-GUI-DCC-001  
**Status:** `implemented_pending_physical_retest` — Code und Unit-Tests grün; **physischer MSI-Nachtest ausstehend**.  
**Payload-Ziel:** `1.10.1.1`

## Zweck

Offline-first HTTP-Server für die Rescue-GUI (`rescue.html`, `auto-e2e-progress.html`) mit Readiness-Gate vor Chromium. BVR-Kern (Backup/Verify/Restore) bleibt unabhängig und läuft bei GUI-Ausfall weiter.

## Lifecycle-Zustände

| Zustand | Bedeutung |
|---------|-----------|
| `not_started` | Launcher/Watchdog noch nicht aktiv; kein HTTP-Prozess. |
| `starting` | `setuphelfer-rescue-ui-launch` gestartet; Preflight läuft. |
| `assets_validating` | Index, Locale-Dateien und Document-Root werden geprüft. |
| `binding` | HTTP-Server-Prozess startet; Socket-Bind ausstehend. |
| `waiting_for_readiness` | Prozess läuft; `/health.json` liefert noch nicht HTTP 200 + `status=ready`. |
| `ready` | Health-Check bestanden; Chromium-Start freigegeben. |
| `chromium_starting` | Grafischer Browser wird gestartet (Kiosk). |
| `visible` | Browser zeigt die UI; Watchdog meldet stabilen Zustand. |
| `degraded` | Server läuft, Browser instabil oder Health schwach (Retry). |
| `fallback_requested` | Watchdog/Launcher fordert TUI-Fallback an. |
| `fallback_active` | TUI-Notmenü aktiv; BVR darf parallel weiterlaufen. |
| `failed` | Endgültiger GUI-Fehler; kein sichtbarer Browser. |
| `stopped` | Graceful Shutdown; HTTP-Prozess beendet. |

## Regeln

1. **Chromium erst nach Readiness** — Browser-Start nur wenn `/health.json` HTTP **200** liefert und `status=ready` ist.
2. **Offener Port ≠ ready** — TCP-Connect oder lauschender Socket allein reicht nicht; Payload-, Entry-Point- und Locale-Validierung sind Pflicht.
3. **Health-Check-Inhalt** — `GET /health.json` muss u. a. enthalten: `payload_version`, `entry_point`, `locale`, `index_exists`, `i18n_validation` (für `auto-e2e-progress.html`).
4. **Watchdog nach Retries** — Nach konfigurierten Readiness-Retries (`SETUPHELFER_RESCUE_UI_READY_RETRIES`, Standard 20) → `rescue.gui.readiness_timeout` oder Prozess-Exit → Fallback.
5. **BVR bei GUI-Fail** — Backup/Verify/Restore/Evidence/Auto-Shutdown des BVR-Kerns werden **nicht** durch GUI-Ausfall blockiert.
6. **Graceful Stop** — Vor Shutdown HTTP-Server beenden (`trap cleanup` in Launcher); Runtime-Status `stopped` schreiben.

## Artefakte

| Pfad | Beschreibung |
|------|--------------|
| `/run/setuphelfer/rescue-ui-status.json` | Launcher-Status (Browser, Server, Display-Modus) |
| `/run/setuphelfer/gui-http-runtime.json` | HTTP-Server-Runtime (PID, Bind, Health, Watchdog) |
| `/run/setuphelfer/gui-http-health.json` | Letzter erfolgreicher Health-Response |
| `SETUP_LOGS/setuphelfer/evidence/boot/*` | Gespiegelte Evidence (best effort) |

## Status-JSON: `rescue-ui-status.json`

```json
{
  "schema_version": 1,
  "ui_url": "http://127.0.0.1:8765/auto-e2e-progress.html",
  "health_url": "http://127.0.0.1:8765/health.json",
  "server_started": true,
  "browser_candidate": "chromium",
  "browser_started": true,
  "display_mode": "kiosk",
  "menu_visible": true,
  "status": "ready",
  "reason": "graphical_browser_starting",
  "network_required": false,
  "telemetry_required": false,
  "rescue_ui": { "server_status": "started", "url": "...", "display_mode": "kiosk", "menu_visible": true, "status": "ready", "reason": "..." },
  "secrets_exposed": false
}
```

## Status-JSON: `gui-http-runtime.json`

```json
{
  "status": "ready",
  "pid": 1234,
  "runtime_user": "root",
  "bind_address": "127.0.0.1",
  "port": 8765,
  "document_root": "/usr/share/setuphelfer/rescue/ui",
  "index_path": "/usr/share/setuphelfer/rescue/ui/auto-e2e-progress.html",
  "health_url": "http://127.0.0.1:8765/health.json",
  "health_status": "ready",
  "asset_validation": "passed",
  "i18n_validation": "passed",
  "chromium_started": false,
  "chromium_visible": false,
  "watchdog_state": "watching",
  "fallback_reason": null,
  "errors": [],
  "warnings": []
}
```

## Status-JSON: `/health.json` (Schema `setuphelfer.rescue.gui-http-health.v1`)

Felder: `status`, `payload_version`, `locale`, `document_root`, `index_path`, `index_exists`, `entry_point`, `i18n_validation`, `i18n_required`, `missing_locales`.

HTTP **503** wenn Index fehlt oder i18n für Progress-Page fehlschlägt; dann `status=failed`.

## Fehlercodes `rescue.gui.*`

| Code | Exit / Kontext | Bedeutung |
|------|----------------|-----------|
| `rescue.gui.document_root_invalid` | Server exit 2 | Document-Root kein Verzeichnis |
| `rescue.gui.index_missing` | Server exit 3 / Launcher exit 2 | Index-HTML fehlt |
| `rescue.gui.bind_failed` | Server exit 4 | Socket-Bind fehlgeschlagen |
| `rescue.gui.server_missing` | Launcher exit 2 | `setuphelfer-rescue-ui-http-server` fehlt |
| `rescue.gui.locale_assets_missing` | Launcher exit 2 | Locale-JSON für Progress-Page fehlt |
| `rescue.gui.port_in_use` | Launcher exit 4 | Port bereits belegt |
| `rescue.gui.process_exited` | Launcher exit 3 | HTTP-Prozess vor Readiness beendet |
| `rescue.gui.readiness_timeout` | Launcher exit 5 | Health nach Retries nicht ready |

**Legacy/Watchdog (kein `rescue.gui.*`-Präfix):** `http_server_failed` — Baseline-Ursache (inline Python `SyntaxError` non-ASCII in bytes literal); behoben durch dedizierten ASCII-safe Server.

## Implementierung

- Server: `scripts/rescue-live/image/setuphelfer-rescue-ui-http-server`
- Launcher: `scripts/rescue-live/image/setuphelfer-rescue-ui-launch`
- Watchdog: `scripts/rescue-live/image/setuphelfer-rescue-gui-watchdog.sh`

## Siehe auch

- [BVR_CORE_FREEZE_PI_RS_BVR_GUI_DCC_001.md](./BVR_CORE_FREEZE_PI_RS_BVR_GUI_DCC_001.md)
- [docs/evidence/rescue/bvr-gui-dcc-001/GUI_HTTP_ROOT_CAUSE_ANALYSIS.md](../evidence/rescue/bvr-gui-dcc-001/GUI_HTTP_ROOT_CAUSE_ANALYSIS.md)
