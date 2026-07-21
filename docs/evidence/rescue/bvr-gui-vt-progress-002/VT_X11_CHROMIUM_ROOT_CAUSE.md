# VT / X11 / Chromium Root Cause – PI-RS-BVR-GUI-VT-PROGRESS-002

## Primäre Ursache (confidence: high)

Der Auto-E2E-Kiosk startet Chromium mit **`auto-e2e-progress.html`**. Der Watchdog akzeptiert die GUI aber nur, wenn:

1. `GET http://127.0.0.1:8765/rescue.html` erfolgreich ist, und
2. `pgrep` ein Pattern `chromium.*rescue\.html` findet.

Folge: Health wird nie grün → Timeout → Chromium wird beendet → `chvt 1` → Operator sieht keine stabile GUI. HTTP-Server und Chromium-Start waren auf diesem Lauf **funktionstüchtig** (`rescue-ui-status.json`, `/health.json`).

## Sekundäre Ursachen

1. **Stale Evidence-Codes:** `gui-watchdog.json` (2026-07-17) und `gui-fallback.json` (`msi_compat_nomodeset`) beschreiben nicht den Boot vom 2026-07-22; `gui-start.log` zeigt VT**7**/openvt.
2. **Fortschrittsdrift:** `physical-progress.json` = `shutdown`, Stick-`auto-e2e-state.json` bleibt `sabrent_waiting` (kein zuverlässiger Final-Mirror / GUI+TUI lesen die Orchestrierungsdatei).
3. **Irreführender Fehlername** `openvt_console_2_not_released` bei Kiosk-VT=7.

## Nicht primär

- `msi_compat_nomodeset` / `pci=noaer`: unter `setuphelfer_mode=gui` ist GUI-Versuch erlaubt; kein Beleg, dass Nomodeset die Sichtbarkeit in diesem Lauf blockierte.
- BVR-Kern: unverändert grün.
