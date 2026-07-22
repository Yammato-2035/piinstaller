# Physical MSI Result – PI-RS-BVR-GUI-VT-PROGRESS-002R

## Verdict

**`passed_with_gui_fallback`** — BVR grün, GUI für den Operator **nicht** sichtbar.

## Run

| Feld | Wert |
|------|------|
| Run-ID | `e2e-rescue-msi-20260722-072255-05b6f187` |
| Boot-ID | `55e3aff7-1533-4a8f-b037-aaad2f38d56c` |
| Gerät | MSI GE63 Raider RGB 8RF / MS-16P5 |
| Payload | **1.10.1.2** |
| Operator | keine grafische Oberfläche |

## BVR

| Schritt | Status |
|---------|--------|
| Backup | passed (162 Dateien, 134 872 183 Bytes) |
| Verify | passed |
| Restore | passed (162 Dateien) |
| Manifest | match |
| Offizieller Import | `import_ok=true` |

## GUI

- HTTP :8765 ready, Entry `auto-e2e-progress.html`, i18n passed
- VT-Auswahl: **7**, `fuser=skip` (kein `fuser -k`)
- `OPENVT_START` geloggt; **kein** Xorg.0.log; `chromium_started=false`, `chromium_visible=false`
- Operator: keine GUI → Fallback faktisch aktiv
- Stale Codes aus älteren Dateien (`openvt_console_2_not_released`, `msi_compat_nomodeset`) **nicht** diesem Boot zugeschrieben

## Progress

- Terminal: `passed` / `shutdown`, Drift = false
- Lücke: Canonical nur `sequence=4`; `bvr.*` am Ende noch `pending` obwohl BVR-Artefakte grün

## Evidence

- Pack: `physical_runs/e2e-rescue-msi-20260722-072255-05b6f187/`
- Offiziell: `docs/evidence/e2e_live_001d/physical_run/e2e-rescue-msi-20260722-072255-05b6f187/`
- JSON: `physical_msi_result.json`
- Vorlauf blockiert: `e2e-rescue-msi-20260722-063452-25718e01`

## Status

**`passed_with_gui_fallback`** — GUI-Sichtbarkeit weiter offen; BVR-Core für Payload 1.10.1.2 physisch bestätigt.
