# GUI HTTP Server Failed (KB)

**Task:** PI-RS-BVR-GUI-DCC-001  
**Code:** `http_server_failed` (Watchdog/Legacy) · Root Cause: inline Python `SyntaxError`

## Symptom

- Keine sichtbare GUI während Auto-E2E
- `rescue-ui-launch.log`: `SyntaxError: bytes can only contain ASCII literal characters`
- `rescue-ui-status.json`: `reason=http_server_failed` oder Prozess-Exit
- BVR läuft weiter → `passed_with_gui_fallback`

## Ursache (Baseline)

`setuphelfer-rescue-ui-launch` startete einen inline-Python-HTTP-Server per Heredoc. Ein non-ASCII-Zeichen (`…`, U+2026) stand in einem `b'...'`-Literal — Python bricht sofort ab.

Referenzlauf: `e2e-rescue-msi-20260721-232222-ba58c7a7`.

## Reparatur (implementiert, physisch offen)

1. Dedizierter Server: `setuphelfer-rescue-ui-http-server` (ASCII-safe)
2. Readiness via `GET /health.json` vor Chromium
3. Locale-Preflight für Progress-Page
4. Payload-Ziel: **1.10.1.1**

## Diagnose

```bash
grep -E 'SyntaxError|rescue\.gui\.' SETUP_LOGS/setuphelfer/logs/boot/rescue-ui-launch.log
curl -fsS http://127.0.0.1:8765/health.json   # nur wenn Server läuft
```

## Fehlercodes `rescue.gui.*`

| Code | Bedeutung |
|------|-----------|
| `rescue.gui.document_root_invalid` | UI-Root fehlt |
| `rescue.gui.index_missing` | HTML fehlt |
| `rescue.gui.bind_failed` | Port/Bind-Fehler |
| `rescue.gui.server_missing` | Server-Skript fehlt |
| `rescue.gui.locale_assets_missing` | Locale-JSON fehlt |
| `rescue.gui.port_in_use` | Port belegt |
| `rescue.gui.process_exited` | Prozess vor Readiness beendet |
| `rescue.gui.readiness_timeout` | Health nicht ready |

## Siehe auch

- [RESCUE_GUI_HTTP_RUNTIME_CONTRACT.md](../../architecture/RESCUE_GUI_HTTP_RUNTIME_CONTRACT.md)
- [GUI_HTTP_ROOT_CAUSE_ANALYSIS.md](../../evidence/rescue/bvr-gui-dcc-001/GUI_HTTP_ROOT_CAUSE_ANALYSIS.md)
