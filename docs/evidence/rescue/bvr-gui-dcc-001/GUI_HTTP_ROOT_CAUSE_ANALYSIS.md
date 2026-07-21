# GUI HTTP Root Cause Analysis – PI-RS-BVR-GUI-DCC-001

## Primary cause (high confidence)

`setuphelfer-rescue-ui-launch` starts an inline Python HTTP server via heredoc.
The default JSON body uses a **non-ASCII** character (`…`, U+2026) inside a **bytes literal** `b'...'`.

Python raises:

```text
SyntaxError: bytes can only contain ASCII literal characters
```

Evidence: `SETUP_LOGS/setuphelfer/logs/boot/rescue-ui-launch.log` from run
`e2e-rescue-msi-20260721-232222-ba58c7a7`.

Consequence:

1. HTTP process exits immediately.
2. `kill -0 $SRV_PID` fails after 1s.
3. Status reason `http_server_failed`.
4. Chromium never starts; watchdog falls back to TUI.
5. BVR continues unattended (correct).

## Secondary observations

- Cmdline correctly requested `setuphelfer_mode=gui` + `msi_e2e_auto=1`.
- `gui-availability.json` / `gui-fallback.json` with `msi_compat_nomodeset` are **misleading leftovers** relative to this boot (cmdline had neither `nomodeset` nor `setuphelfer_msi_compat=1`; `should_disable_gui_for_msi_compat` returns false when `mode=gui`).
- Document root and `auto-e2e-progress.html` were present (inject verified).
- Port conflict not indicated; process never bound.

## Repair strategy

1. Move HTTP server to a dedicated ASCII-safe Python script (no non-ASCII bytes literals).
2. Add readiness/health endpoint with payload/build metadata.
3. Start Chromium only after readiness.
4. Keep watchdog fallback.
5. Localize progress page (de/en/fr/nl) without embedding non-ASCII in bytes literals.
