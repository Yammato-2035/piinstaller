# HARDWARE_DISCOVERY_IST_AUDIT — PI-RS-HW-COMPAT-PROVISION-001

Stand: 2026-08-03, Branch `pi-rs-hw-compat-provision-001` (Basis `origin/main` @ `b8651d33`).

Zweck: Vollständige Ist-Aufnahme bestehender Hardware-/Rescue-Erkennungslogik, bevor
neue Module (`backend/core/hardware_contracts.py` etc.) angelegt werden. Ziel: keine
Duplikate, klare Abgrenzung "wer besitzt was".

## Zusammenfassung

Es existieren **zwei getrennte Hardware-Erkennungspfade** im Repository, die
unterschiedliche Zwecke verfolgen und **nicht verschmolzen** werden dürfen:

1. **Produkt-App-Pfad** (`backend/core/hardware_discovery.py`,
   `backend/core/system_info_facade.py`, `backend/modules/raspberry_pi_config.py`):
   liefert Anzeige-Werte für die laufende Desktop-/Pi-Installer-App (System-Info-Tab,
   Pi-Konfigurationsseite). Fokus: hübsche Kurzbezeichnungen (z. B. "NVIDIA GeForce RTX
   4070"), Temperaturen, RAM-Module, Pi-Config-Optionen lesen/schreiben.
2. **Rescue-Assessment-Pfad** (`backend/core/rescue_system_assessment_v2.py` +
   `rescue_issue_codes_v2.py` + `rescue_recommendation_codes_v2.py` +
   `rescue_assessment_redaction.py`): liefert einen groben, redigierten
   Systemzustand für den Rettungsstick-Bericht (Vendor-Listen, keine Pro-Gerät-Modelle).

Beide Pfade sind auf **Erkennung von Vendor/Produktnamen**, nicht auf **Betriebszustand
pro Einzelgerät** ausgelegt. Es gibt noch **keine** normalisierte
Gerät-für-Gerät-Modellierung mit Treiber-/Firmware-/Betriebsstatus-Trennung
(`HardwareDevice` im Sinne dieser Phase existiert nicht).

`backend/core/driver_catalog.py` und `backend/core/rescue_peripheral_discovery.py`
(referenziert in einem separaten, noch **nicht gemergten** PR
`claude/projekt-bewertung-setup-hts9w7`) existieren auf `main` **nicht**. Kein Konflikt
mit dieser Phase, aber im finalen Review beachten, falls jener PR vor diesem gemergt wird.

## Tabelle

| Bereich | vorhandene Implementierung | Reife | Duplikatrisiko | nächste Maßnahme |
|---|---|---|---|---|
| CPU-Erkennung (x86) | `hardware_discovery.get_cpu_summary/get_cpu_name` (lscpu, /proc/cpuinfo); `rescue_system_assessment_v2._collect_cpu_ram` (lscpu grob) | mittel (Anzeige-Strings, kein Modell) | mittel | `cpu_platform_detection.py`: strukturiertes `HardwareDevice`, delegiert Rohdaten-Parsing nicht neu, liest sysfs/lscpu selbst (read-only), aber übernimmt keine Anzeige-Logik |
| Raspberry-Pi-Modellerkennung | `raspberry_pi_config.py::_detect_pi_model` (Device-Tree-String → pi1..pi5, RAM) | niedrig (keine 3B+/400/CM4/CM5-Unterscheidung, kein `/proc/device-tree/compatible`) | hoch für Basis-Modellstring-Lesen | `raspberry_pi_detection.py` liest zusätzlich `compatible`, Bootloader/EEPROM-Status (lesend), delegiert NICHT an `RaspberryPiConfigModule` (andere Concern: Live-Konfiguration vs. Rescue-Kompatibilitätsbewertung); beide dürfen unabhängig denselben Rohpfad lesen |
| Pi-Konfiguration lesen/schreiben | `raspberry_pi_config.py::read_config/write_config` | hoch (Produktfeature) | keins | unverändert lassen, nicht anfassen |
| Mainboard/Chipsatz (DMI) | `hardware_discovery.get_motherboard_info` (board_vendor/name via sysfs/dmidecode); `rescue_system_assessment_v2._collect_system` (dmidecode system) | niedrig (kein Chipsatz-ID/PCI-Zuordnung, kein `review_required`-Konzept) | mittel | `mainboard_chipset_detection.py`: übernimmt DMI-Lesepfad-Muster (sysfs zuerst, dmidecode Fallback), fügt Chipsatz-ID-Zuordnung + `review_required`-Schwelle hinzu |
| GPU-Erkennung | `hardware_discovery._get_gpus_for_system_info` (lspci -k, nvidia-smi, Anzeige-Namen-Bereinigung); `rescue_system_assessment_v2._collect_gpu` (Vendor-Liste, `nvidia_compat_mode_detected`) | mittel (Anzeige-fokussiert, keine DRM/Connector/nomodeset-Prüfung) | hoch (Namensbereinigung nicht duplizieren) | `gpu_detection.py` liest PCI/DRM/sysfs selbst für Statusmodell, ruft für Anzeige-Namen optional `hardware_discovery._clean_gpu_description` wieder, statt neu zu schreiben |
| USB-Geräte | keine dedizierte Klassifikation gefunden (nur lsusb-Erwähnungen in Diagnose-Skripten) | keine | keins | `usb_device_detection.py` neu, keine Kollision |
| Tastatur/Maus/Input | keine dedizierte Erkennung; `PeripheryScan.tsx` (Frontend) zeigt vermutlich andere Peripherie (Netzwerk/Drucker via CUPS, nicht Input-Devices) | keine (Backend) | keins | `input_device_detection.py` neu |
| Drucker/Scanner | `frontend/src/pages/PeripheryScan.tsx` + zugehörige Backend-Handler (`control_center_handlers.py` u. a.) — bestehendes CUPS/Netzwerk-Feature für den **Produkt-App**-Kontext (nicht Rescue-Stick) | mittel (Produktfeature, andere Zielgruppe) | mittel (Verwechslungsgefahr Produkt- vs. Rescue-Kontext) | `backend/peripherals/printer_detection.py` etc. sind **Rescue-Stick-spezifisch** (read-only, kein CUPS-Queue-Management); getrennter Namensraum `backend/peripherals/` vermeidet Kollision mit Produkt-App-Modulen |
| Treiber-/Firmware-Resolver | keine generische Resolver-Pipeline; nur Ad-hoc-Strings (`nvidia_compat_mode_detected`, `dmesg_missing_firmware_redacted`) | niedrig | keins strukturell, aber Konzept überlappt mit `rescue_system_assessment_v2` Missing-Firmware-Erkennung | `driver_resolver.py`/`firmware_resolver.py` neu; `rescue_system_assessment_v2` bleibt eigenständig (grobes Assessment für Bericht), Resolver liefert Pro-Gerät-Plan |
| Kuratierter Hardwarekatalog | keine strukturierte JSON-DB; ASUS-/MSI-Wissen liegt nur als Freitext-Evidence unter `docs/evidence/rescue-stick/*.md` (z. B. `kernel-pin-g513qm.md`, `RS-*-20260802.md`) | evidence-only | keins (reine Dokumentation, kein Code) | `data/hardware/hardware_compat_catalog.json` neu, referenziert bestehende Evidence-Pfade statt sie zu duplizieren |
| Safety-/Storage-/Mount-Facades | `backend/core/safe_device.py` (`validate_write_target`, Klassifikation), `backend/core/storage_facade.py` (`get_block_devices`, `get_block_device_size_bytes`, Klassifikation), `backend/core/mount_facade.py` (Mount-Snapshot/Klassifikation), `backend/core/device_identity.py` (stabile Geräte-Identität) | hoch, gut getestet | **hoch, falls neu implementiert** | Carrier-Planer (Phase 12) MUSS `storage_facade.get_block_devices`/`get_block_device_size_bytes` für reale Byte-Werte verwenden, KEINE eigene lsblk-Logik |
| Telemetrie-Redaction | `backend/core/rescue_assessment_redaction.py` (`redact_assessment_payload`, `scan_forbidden_fields`) für das v2-Assessment-Schema | hoch für sein Schema | mittel | Neuer `hardware_inventory_summary_v1`-Contract (Phase 16) nutzt eigene, engere Redaction-Funktion (anderes Schema), verweist aber auf dieselben Verbotslisten (Seriennummern, MAC, IP) |
| DCC-Produktstatus | `backend/core/dcc_status_facade.py` (`build_dcc_status_overview`, `build_dcc_roadmap_overview`, ...) | hoch | keins | neue Statusfelder additiv ergänzen, bestehende Funktionen nicht umschreiben |
| Image-Katalog / OS-Provisionierung | keine gefunden (`deploy/source_registry.py`, `deploy/cache_plan.py` betreffen Setuphelfer-Selbst-Deployment, nicht Ziel-OS-Images) | keine für Ziel-OS | keins | `backend/provisioning/*` komplett neu, getrennter Namensraum von `backend/deploy/` (das ist Setuphelfer-Eigen-Deployment) |
| API-Router-Registrierung | `backend/api/routes/rescue.py` (optionale Sub-Router via try/except ImportError), `backend/app.py` direkte `include_router(...)`-Aufrufe, `backend/app_bootstrap/router_registry.py` für Non-Rescue-Router | hoch, etabliertes Muster | keins | neue `api/routes/rescue_hardware.py`, `rescue_peripherals.py`, `rescue_platform.py`, `rescue_carrier.py`, `rescue_provisioning.py` folgen demselben Muster |
| Rescue-UI | `frontend/src/rescue/RescueApp.tsx`, `RescueBootStatus.tsx`, `rescueTypes.ts` (Rescue-TUI/Boot-Overlay, kein Hardware-Dashboard) | mittel, aber anderer Zweck (Boot-Status, nicht Hardware-Inventar) | niedrig | neue Hardware-Übersichtsseite ergänzt, ersetzt nichts |

## Nicht dupliziert — bewusste Abgrenzung

- `raspberry_pi_config.py` bleibt alleiniger Besitzer von Pi-**Konfiguration**
  (Lesen/Schreiben von `/boot/config.txt`-Optionen). Diese Phase fügt nur
  **Kompatibilitäts-/Boot-Bewertung** hinzu, keine Config-Schreiblogik.
- `rescue_system_assessment_v2.py` bleibt alleiniger Besitzer des groben
  Rescue-Berichts-Schemas (`system-assessment.v2`). Diese Phase fügt ein
  **feingranulares Pro-Gerät-Modell** parallel hinzu, ersetzt das Assessment nicht.
- `safe_device.py` / `storage_facade.py` / `mount_facade.py` bleiben alleinige
  Besitzer von Schreibschutz/Klassifikation für Massenspeicher. Der
  64-GB-Carrier-Planer (Phase 12) und Provisionierungsplan (Phase 13) rufen diese
  Facades auf, statt eigene Storage-/Mount-Logik zu schreiben.
- `hardware_discovery.py` bleibt alleiniger Besitzer der **Anzeige**-Aufbereitung
  (Kurzbezeichnungen) für die Produkt-App. Neue Module dürfen seine reinen
  Parsing-Helfer (`_clean_gpu_description`) wiederverwenden, aber keine Kopie anlegen.

## Risikohinweis PR #4 (nicht gemergt)

Der offene Draft-PR `claude/projekt-bewertung-setup-hts9w7` fügt
`backend/core/driver_catalog.py` und `backend/core/rescue_peripheral_discovery.py`
hinzu. Diese existieren auf `main` (Basis dieser Phase) nicht. Falls beide PRs
gemergt werden, ist ein Merge-Review auf Namensüberlappung
(`driver_catalog` vs. neuer `driver_resolver`/`hardware_compat_catalog`)
erforderlich — **kein Blocker** für diese Phase, da diese Phase auf einer eigenen
Basis arbeitet und keine Annahmen über jenen PR trifft.
