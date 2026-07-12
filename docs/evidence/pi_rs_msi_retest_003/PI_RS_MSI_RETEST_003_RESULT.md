# PI-RS-MSI-RETEST-003 — Ergebnis

**Status:** `review_required`  
**Repository:** `main @ 60440cdd`  
**Session:** `20260712_225043_boot` / `40d8b1a9-c7ee-4026-b48a-3d38bd635d4d`  
**Payload:** 1.10.0.16

## Pre-Boot (Entwicklungsrechner)

Payload, Versionsträger und Gates auf dem Stick vor dem Boot vollständig verifiziert (`ready_for_physical_boot=true`).

## Physischer Boot — positive Befunde

| Kriterium | Ergebnis |
|-----------|----------|
| Payload 1.10.0.16 / SHA256 | verifiziert (Pre-Boot + Runtime `/api/version`) |
| MSI-Compat Kernelparameter | `setuphelfer_msi_compat=1 nomodeset nouveau.modeset=0 pci=noaer` |
| `x11_starting` in aktueller Timeline | **nein** (3 Phasen, kein x11) |
| GUI verfügbar | nein (`msi_compat_nomodeset`) |
| openvt / chvt / startx / Xorg | nicht ausgeführt (gui-fallback, kein Xorg-Log) |
| Neue Session-ID / Boot-ID | ja, Payload 1.10.0.16 |
| Stale Logs als aktuell | **nein** (rescue-ui-status.json nicht importiert) |
| Interne Platte beschrieben | nein |
| Operator: TUI ≥120 s stabil | **ja** |
| Operator: keine visuelle Beschädigung | **ja** |

## Evidence-Lücken (Grund für review_required)

1. **`tui_mode_selected` fehlt** in `boot-timeline.jsonl` der Session (nur `systemd_started` + `rescue_boot_status_visible`).
2. **Automatische Erfassung sehr früh:** Diagnostics-Uptime ~11 s; Console-Owner noch `boot_progress`.
3. Kein `console-ownership` mit `owner=tui` in importierter Session.
4. Operator-Fotos nicht im Repository.

## Session-Isolation

Import ausschließlich:

- `diagnostics/20260712_225040_early`
- `diagnostics/20260712_225043_boot`
- aktuelle `evidence/msi-rs011b/boot-timeline.jsonl` (3 Zeilen)
- `evidence/boot/gui-availability.json`, `gui-fallback.json`, `boot_state_redacted.json`

**Nicht importiert:** `20260712_015835`, `20260712_111206_boot`, aggregiertes `evidence/boot/boot-timeline.jsonl`, stale `rescue-ui-status.json`.

## Bewertung

Unter dem MSI-Kompatibilitätsprofil blockiert die GUI korrekt; in der **aktuellen Session-Timeline** erscheint kein `x11_starting`. Der Operator bestätigt eine **stabile TUI ≥120 Sekunden** ohne visuelle Beschädigung.

Für **`passed`** fehlt jedoch die maschinell belegte Timeline (`tui_mode_selected`, Console-Handoff an `tui`). Daher **`review_required`**, nicht `passed`.

**Nicht behaupten:** „Die GUI funktioniert auf dem MSI.“

## Nächste Schritte

- Optional: erneuter Boot mit manueller Spät-Evidence (Timeline + Console-Ownership nach TUI-Handoff)
- Oder: Acceptance-Lücke akzeptieren und PI-RS-TEL-LIVE-001 erst nach expliziter Freigabe
- Bei erneutem TUI-Failure: PI-RS-MSI-GUI-004
