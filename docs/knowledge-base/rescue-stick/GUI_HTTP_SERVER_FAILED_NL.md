# GUI HTTP-server mislukt (KB)

**Task:** PI-RS-BVR-GUI-DCC-001  
**Code:** `http_server_failed` (watchdog/legacy) · Oorzaak: inline Python `SyntaxError`

## Symptoom

- Geen zichtbare GUI tijdens auto-E2E
- `rescue-ui-launch.log`: `SyntaxError: bytes can only contain ASCII literal characters`
- `rescue-ui-status.json`: `reason=http_server_failed` of proces exit
- BVR gaat door → `passed_with_gui_fallback`

## Oorzaak (baseline)

De launcher startte een inline Python HTTP-server via heredoc. Een non-ASCII-teken (`…`, U+2026) in een `b'...'`-literal veroorzaakte onmiddellijke afsluiting.

Referentierun: `e2e-rescue-msi-20260721-232222-ba58c7a7`.

## Fix (geimplementeerd, fysieke retest open)

1. Dedicated server: `setuphelfer-rescue-ui-http-server` (ASCII-safe)
2. Readiness via `GET /health.json` vóór Chromium
3. Locale-preflight voor progress-pagina
4. Payload-doel: **1.10.1.1**

## Diagnose

```bash
grep -E 'SyntaxError|rescue\.gui\.' SETUP_LOGS/setuphelfer/logs/boot/rescue-ui-launch.log
curl -fsS http://127.0.0.1:8765/health.json
```

## Codes `rescue.gui.*`

Zie [RESCUE_GUI_HTTP_RUNTIME_CONTRACT.md](../../architecture/RESCUE_GUI_HTTP_RUNTIME_CONTRACT.md).

## Zie ook

- [GUI_HTTP_ROOT_CAUSE_ANALYSIS.md](../../evidence/rescue/bvr-gui-dcc-001/GUI_HTTP_ROOT_CAUSE_ANALYSIS.md)
