# GUI HTTP Server Failed (KB)

**Task:** PI-RS-BVR-GUI-DCC-001  
**Code:** `http_server_failed` (watchdog/legacy) · Root cause: inline Python `SyntaxError`

## Symptom

- No visible GUI during auto-E2E
- `rescue-ui-launch.log`: `SyntaxError: bytes can only contain ASCII literal characters`
- `rescue-ui-status.json`: `reason=http_server_failed` or process exit
- BVR continues → `passed_with_gui_fallback`

## Root cause (baseline)

`setuphelfer-rescue-ui-launch` started an inline Python HTTP server via heredoc. A non-ASCII character (`…`, U+2026) inside a `b'...'` literal caused immediate exit.

Reference run: `e2e-rescue-msi-20260721-232222-ba58c7a7`.

## Fix (implemented, physical retest pending)

1. Dedicated server: `setuphelfer-rescue-ui-http-server` (ASCII-safe)
2. Readiness via `GET /health.json` before Chromium
3. Locale preflight for progress page
4. Payload target: **1.10.1.1**

## Diagnosis

```bash
grep -E 'SyntaxError|rescue\.gui\.' SETUP_LOGS/setuphelfer/logs/boot/rescue-ui-launch.log
curl -fsS http://127.0.0.1:8765/health.json   # only if server is running
```

## Error codes `rescue.gui.*`

| Code | Meaning |
|------|---------|
| `rescue.gui.document_root_invalid` | UI root missing |
| `rescue.gui.index_missing` | HTML missing |
| `rescue.gui.bind_failed` | Bind/port failure |
| `rescue.gui.server_missing` | Server script missing |
| `rescue.gui.locale_assets_missing` | Locale JSON missing |
| `rescue.gui.port_in_use` | Port in use |
| `rescue.gui.process_exited` | Process exited before readiness |
| `rescue.gui.readiness_timeout` | Health never ready |

## See also

- [RESCUE_GUI_HTTP_RUNTIME_CONTRACT.md](../../architecture/RESCUE_GUI_HTTP_RUNTIME_CONTRACT.md)
- [GUI_HTTP_ROOT_CAUSE_ANALYSIS.md](../../evidence/rescue/bvr-gui-dcc-001/GUI_HTTP_ROOT_CAUSE_ANALYSIS.md)
