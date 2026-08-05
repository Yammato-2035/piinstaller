# PI-RS-HW-BASELINE-DIAG-I18N-002 — Phase 1: Ist-Stand-Audit

Datum: siehe Git-Commit-Zeitstempel. Ausgangsbranch: `origin/pi-rs-hw-compat-provision-001` (HEAD `dfa9ae18`).

## Zweck

Bevor neue Hardware-Baseline-Diagnostik (RAM/CPU/GPU/HDD/SATA-SSD/NVMe) implementiert wird,
prüft dieses Dokument, was im Repository bereits existiert, um Duplikate zu vermeiden.

## Methodik

Durchsucht: `backend/`, `frontend/src/`, `scripts/`, `docs/` nach:

- `meminfo|memory|edac|mce|machine.check|thermal|throttl`
- `smartctl|nvme smart|nvme-cli|reallocated|pending_sector|media_errors`
- `drm|renderD|glxinfo|eglinfo|vulkaninfo|gpu.*test`
- `baseline|preflight|health_gate|hardware_gate`

## Ergebnis pro Bereich

### RAM / EDAC / MCE / OOM

**Nicht vorhanden.** Es gibt keine Auswertung von `/proc/meminfo`, `dmidecode`-RAM-Modulen,
EDAC-Zählern, Machine-Check-Fehlern oder OOM-Historie. `backend/core/hardware_contracts.py`
und `backend/core/hardware_inventory.py` (aus PI-RS-HW-COMPAT-PROVISION-001) liefern nur
generische Geräteinventur, keine Speicher-Gesundheitsprüfung. → **Neu zu erstellen**, keine
Duplikation möglich.

### CPU-Baseline (jenseits reiner Plattformerkennung)

`backend/core/cpu_platform_detection.py` liefert Architektur/Modell/Kerne/Virtualisierung/
Microcode-Anzeige (reine Inventur, read-only). Es gibt **keine** Prüfung auf MCE/Hardware-Error/
Thermal-Throttling/Quick-Probe. → Baseline-Modul **baut auf** `cpu_platform_detection.py` auf
(reuse), fügt aber ausschließlich neue Prüfungen hinzu — keine Duplikation.

### GPU-Baseline

`backend/core/gpu_detection.py` und `backend/core/gpu_driver_resolver.py` erkennen GPU-PCI-
Geräte, gebundene Treiber, Firmware-/Kernelparameter-Status (aus Vorgängerphase). Es fehlen:
DRM-Card-/Render-Node-Prüfung, Kernel-/DRM-Fehler-Scan, optionale `glxinfo`/`eglinfo`/
`vulkaninfo`-Probes. → Baseline-Modul **reuses** `build_gpu_report()` als Eingabedaten, fügt
zusätzliche, rein additive Prüfungen hinzu.

### Storage-Diagnostik (SMART/NVMe)

`backend/core/rescue_msi_diagnostics.py`, `backend/modules/inspect_storage.py` enthalten
vereinzelte, grobe SMART/Storage-Signale (primär für MSI-Windows-Rescue-Kontext, nicht als
allgemeine Baseline-Gesundheitsprüfung konzipiert). Es gibt **keine** attributgenaue Auswertung
von Pending Sectors, Reallocated Sectors, NVMe Available Spare/Percentage Used/Media Errors
usw. `backend/core/storage_facade.py` liefert Block-Device-Inventur (lsblk-basiert), aber keine
Geräteklassen-Ermittlung (rotational/nvme/usb_bridge) und keine SMART-Attributparsing. →
**Neu zu erstellen**: `storage_health_normalizer.py` (Geräteklasse) + `storage_baseline_
diagnostics.py` (gemeinsame Prüfungen) + `hdd_/sata_ssd_/nvme_baseline_diagnostics.py`
(gerätespezifisch). `storage_facade.py` wird für die Geräteliste **reused**, nicht dupliziert.

### Baseline-/Preflight-/Health-Gate

Treffer für `baseline|preflight|health_gate|hardware_gate` betreffen ausschließlich **andere**,
bestehende Konzepte: Restore-Preview-Gates, Backup-Guards, ISO-Build-Gates, Safety-Facade
(`backend/core/safety_facade.py`). Keiner davon prüft Hardware-Gesundheit vor einem Rescue-Lauf.
→ **Neu zu erstellen**: `backend/rescue/hardware_baseline_gate.py`. Wichtig: Dieses Gate ist
**additiv** — es ersetzt und umgeht `safety_facade.py` **nicht**, sondern wird zusätzlich davor
geschaltet.

### Vier-Sprachen-Dokumentationsmuster

Bestehende Konvention (aus PI-RS-HW-COMPAT-PROVISION-001 Phase 15/19 und älteren Rescue-
Dokumenten): sprachgetrennte Dateien mit Suffix `_DE.md`/`_EN.md` (aktuell nur DE/EN
vollständig; FR/NL fehlen). Frontend-i18n (`frontend/src/rescue/i18n/{de,en,fr,nl}.json`) ist
bereits **vollständig vierschprachig** angelegt (DE/EN/FR/NL), nur ohne die neuen Baseline-Keys.
→ Diese Phase folgt der bestehenden Namenskonvention, führt **keine** konkurrierende Struktur ein.

### DCC-Status / Telemetrie-Redaction

`backend/core/telemetry_redaction_contract.py` und `backend/core/hardware_dcc_status.py`
(aus PI-RS-HW-COMPAT-PROVISION-001 Phase 16) definieren bereits das Redaction-Muster
(keine Seriennummern/MAC/IP in Telemetrie). Die neue Baseline-Telemetrie **folgt** demselben
Muster, dupliziert es aber nicht.

## Zusammenfassung: Wiederverwendung vs. Neubau

| Bereich | Wiederverwendet | Neu |
|---|---|---|
| CPU-Inventur | `cpu_platform_detection.py` | MCE/Thermal/Quick-Probe |
| GPU-Inventur | `gpu_detection.py`, `gpu_driver_resolver.py` | DRM/Render-Node/Kernel-Fehler/Probes |
| Storage-Geräteliste | `storage_facade.py` | Geräteklasse, SMART/NVMe-Attribute |
| Safety | `safety_facade.py` (bleibt maßgeblich) | additives Baseline-Gate |
| i18n-Struktur | bestehende `_DE/_EN/_FR/_NL`-Konvention, JSON-i18n-Locale | neue Baseline-Dokumente/Keys |
| RAM | — (nichts vorhanden) | vollständig neu |

Kein bestehendes Modul wird dupliziert; alle neuen Baseline-Module sind additive Erweiterungen.
