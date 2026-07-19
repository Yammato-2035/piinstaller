# PI-RS-MSI-GUI-002 — Disable GUI under MSI Compat

## Ausgangslage

- Payload **1.10.0.14** auf Intenso Ultra Line Stick
- MSI GE63 Session **20260712_015835** mit MSI-Compat (`setuphelfer_msi_compat=1`, `nomodeset`, `pci=noaer`)
- **1.10.0.14** behoben: Console-Shield, kein tty1-Clear während Boot, Textmodus stabil, PCIe-AER ruhig
- **Weiterhin defekt:** GUI unter MSI-Compat; `openvt: Konsole 2 konnte nicht freigegeben werden`; kein Xorg; GUI-Watchdog/chvt zerstört whiptail optisch

## Entscheidung

Auf GE63/MSI-Compat/nomodeset ist **Textmodus die Primär-UI**. GUI wird nicht automatisch oder über den Menüpunkt gestartet.

## Fixes (Payload 1.10.0.15)

- Zentrale Erkennung: `setuphelfer_rescue_should_disable_gui_for_msi_compat`
- Status: `/run/setuphelfer/gui-availability.json` (`gui_available=false`, `openvt_allowed=false`, …)
- TUI-Menü „Grafische Oberfläche starten“ zeigt Operator-Meldung, kein openvt/chvt/startx
- GUI-Watchdog blockiert früh unter MSI-Compat (kein chvt 2)
- `setuphelfer_rescue_run_on_kiosk_vt` blockiert openvt/chvt unter MSI-Compat
- TUI-Rerender nach blockiertem/fehlgeschlagenem GUI-Wunsch
- Lab-Telemetry-Scripts unverändert enthalten

## Operator-Meldung

```text
Grafische Oberfläche auf diesem Gerät im MSI-Kompatibilitätsmodus nicht verfügbar.

Grund:
nomodeset / VT-Übernahme ist auf diesem Gerät nicht stabil.

Bitte Textmodus nutzen.
```

## Payload 1.10.0.15

| Feld | Wert |
|---|---|
| Artefakt | `build/rescue/filesystem.squashfs.repacked-1.10.0.15` |
| SHA256 | `307ae9a381e2792fddd2ca8ebb6c20550544f0b167e2461c323c596651ecd318` |
| USB-Write | **nicht durchgeführt** |

## Tests

- `backend/tests/test_pi_rs_msi_gui002_*.py`
- `scripts/check-rescue-payload-msi-gui002-content.sh`
- `scripts/smoke-pi-rs-msi-gui002-disable-gui-under-msi-compat.sh`

## Nächster Schritt

**Abgeschlossen:** PI-RS-USB-MSI-GUI-002 (USB 1.10.0.15) — physischer Retest **failed** (PI-RS-MSI-RETEST-002).

**Folge-Sprint:** [PI-RS-MSI-GUI-003](PI_RS_MSI_GUI_003_TUI_CONSOLE_ISOLATION.md) — Payload **1.10.0.16**, TUI/Console-Isolation. Nächste Operator-Schritte: **PI-RS-USB-UPDATER-001** + **PI-RS-MSI-RETEST-003**.
