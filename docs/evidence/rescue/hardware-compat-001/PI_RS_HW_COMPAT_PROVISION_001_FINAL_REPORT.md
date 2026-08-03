# Abschlussbericht — PI-RS-HW-COMPAT-PROVISION-001

Hardware-Erkennung, Treiberauflösung, Raspberry-Pi-Unterstützung und
64-GB-Provisionierungsorchestrator (Grundlagenphase)

## 1–6. Workspace / Repository / Branch / Commits

| Feld | Wert |
|---|---|
| Ausgangs-Workspace | `/home/volker/piinstaller` |
| Ziel-Workspace | `/tmp/piinstaller-hw-compat-provision-001` (Git-Worktree) |
| Repository | `piinstaller` (`https://github.com/Yammato-2035/piinstaller.git`) |
| Branch | `pi-rs-hw-compat-provision-001` |
| Ausgangs-HEAD | `b8651d33` ("Complete MSI 1.10.0.16 late console ownership evidence") |
| Ziel-Basis | `origin/main` @ `b8651d33` |
| End-HEAD | `caca9fa8` |
| origin/main (aktuell, nach Fetch) | `b8651d33` (unverändert — kein Merge nach main) |
| Push | `origin/pi-rs-hw-compat-provision-001` erfolgreich, kein automatischer Merge |

**9 Commits** (wie in Phase 21 spezifiziert, jeweils gezielt gestagt, kein `git add -A`):

1. `2778cedf` Add normalized hardware inventory contracts
2. `524432c3` Add CPU GPU mainboard and USB detection
3. `0aa00417` Add printer scanner and input device detection
4. `ca030834` Add driver and firmware resolution plans
5. `187181f1` Add Raspberry Pi 3 to 5 compatibility model
6. `199b432a` Add 64GB carrier and OS catalog planning
7. `cd598a01` Add rescue hardware APIs and UI
8. `966d634f` Add telemetry redaction and DCC status
9. `caca9fa8` Add tests evidence documentation and i18n

**Diffstat gesamt:** 104 Dateien geändert, 9.455 Zeilen hinzugefügt, 17 Zeilen entfernt.

## 8. Geänderte Dateien nach Bereich

| Bereich | Neue Dateien | Geänderte Dateien |
|---|---|---|
| `backend/core/` (Contracts, CPU/GPU/Mainboard/USB/Input, Resolver, Katalog, Telemetrie, DCC) | 15 | 2 (`dcc_status_facade.py`, `app.py`) |
| `backend/peripherals/` (Drucker/Scanner) | 6 | 0 |
| `backend/platforms/` (Raspberry Pi) | 5 | 0 |
| `backend/rescue/` (Carrier) | 3 | 0 |
| `backend/provisioning/` (OS-Katalog/Plan) | 5 | 0 |
| `backend/api/routes/` | 5 | 1 (`dev_dashboard_readonly.py`) |
| `backend/tests/` | 19 | 1 (`test_rescue_gui_visual_contract_v1.py`, Tile-Count-Fix) |
| `data/hardware/`, `data/provisioning/` | 6 | `.gitignore` (Ausnahme ergänzt) |
| `frontend/src/rescue/` | 2 | 9 (Nav-Tiles, Dashboard, App, Theme, i18n×4, CSS) |
| `docs/architecture/`, `docs/rescue-stick/`, `docs/knowledge-base/`, `docs/faq/` | 11 | 0 |
| `docs/evidence/rescue/hardware-compat-001/` | 5 (inkl. dieser Bericht) | 0 |
| `docs/roadmap/`, `CHANGELOG.md` | 0 | 2 |
| Versionsdateien (`VERSION`, `config/version.json`, `frontend/package*.json`, `Cargo.toml`, `tauri.conf.json`, `setuphelfer-version.json`, `deb-changelog.txt`, `package.json`) | 0 | 8 |

## 9. Erkannte bestehende Module (keine Duplikate angelegt)

- `backend/core/hardware_discovery.py` + `system_info_facade.py` (Produkt-App-Anzeigepfad) — unverändert, weiterhin alleiniger Besitzer der Anzeige-Kurzbezeichnungen.
- `backend/core/rescue_system_assessment_v2.py` (grobes Rescue-Bericht-Schema) — unverändert.
- `backend/modules/raspberry_pi_config.py` (Pi-Konfiguration lesen/schreiben) — unverändert, bleibt alleiniger Besitzer der Config-Schreiblogik.
- `backend/core/safe_device.py`, `storage_facade.py`, `mount_facade.py`, `device_identity.py` — unverändert; vom Carrier-Planer **wiederverwendet** (`storage_facade.get_block_device_size_bytes` statt eigener `lsblk`-Logik).
- `backend/core/rescue_assessment_redaction.py` — unverändert; neuer, engerer Telemetrie-Contract ergänzt eigenständig.
- `backend/core/dcc_status_facade.py` — additiv erweitert (`build_dcc_hardware_provisioning_section`), bestehende Funktionen unverändert.
- Vollständige Analyse: `docs/evidence/rescue/hardware-compat-001/HARDWARE_DISCOVERY_IST_AUDIT.md`.

## 10. Neu geschaffene Contracts

`HardwareInventory`, `HardwareDevice`, `HardwareDriverState`, `HardwareFirmwareState`,
`HardwareCapability`, `HardwareIssue`, `HardwareRecommendation`,
`HardwareEvidenceReference`, `PlatformIdentity`, `PeripheralCapability`
(`backend/core/hardware_contracts.py`); `DriverPlan`
(`backend/core/driver_resolver.py`); Carrier-Kapazitätsplan
(`backend/rescue/carrier_capacity_planner.py`); `OsInstallPlan`
(`backend/provisioning/os_install_plan.py`); `hardware_inventory_summary_v1`
Telemetrie-Contract (`backend/core/hardware_telemetry_contract.py`).

## 11. Unterstützte Hardwareklassen (Erkennung/Klassifikation, kein Aktivierungsnachweis)

CPUs/SoCs, GPUs/Grafikpfade, Mainboards/Chipsätze, PCI-/PCIe-Geräte,
USB-Geräte, Massenspeicher/Controller, Netzwerkadapter, Tastaturen/Mäuse,
Drucker (Matrix/Tintenstrahl/Laser/Mono/Farbe/MFP), Scanner, Raspberry Pi 3–5
(inkl. Varianten), Multi-Arch-Provisionierungsvorbereitung.

## 12. CPU-/GPU-/Mainboard-Erkennungsstand

Implementiert und fixture-getestet: Architektur-/Hersteller-/Familien-/
Modellerkennung, Virtualisierungsflags (`cpu_platform_detection.py`);
DMI+PCI-Host-Bridge-basierte Mainboard-/Chipsatz-Erkennung mit
`review_required`-Schwelle statt Raten (`mainboard_chipset_detection.py`);
GPU-Erkennung mit getrennten Zuständen erkannt/Treiber gebunden/Modul
geladen/Firmware/DRM/`nomodeset` (`gpu_detection.py`, `gpu_driver_resolver.py`).
**Keine physische Verifikation** in dieser Phase.

## 13. USB-/Input-Erkennungsstand

Generische USB-Klassifikation inkl. Multifunktionsgeräte-Modell mit
getrennten Capabilities (`usb_device_detection.py`); Eingabegeräte ohne
Erfassung von Eingabedaten (`input_device_detection.py`). Fixture-getestet,
**keine physische Verifikation**.

## 14. Drucker-/Scanner-Erkennungsstand

IPP/CUPS/PPD-basierte Druckererkennung mit `unknown`/`review_required` bei
unzureichender Datenlage (`peripherals/printer_detection.py` +
`printer_driver_resolver.py`); SANE/scanimage-basierte Scannererkennung
(`scanner_detection.py` + `scanner_driver_resolver.py`). Fixture-getestet,
**keine physische Verifikation**, kein automatischer Test-Druck/-Scan.

## 15. Treiber-/Firmware-Resolver-Stand

8-stufiger Resolver implementiert (`driver_resolver.py`), Firmwarestatus
getrennt bewertet (`firmware_resolver.py`), sicherer, ausschließlich
vorschauender Aktivierungsplan (`driver_activation_plan.py`). Kuratierter
Kompatibilitätskatalog mit MSI-GE63-/ASUS-G513QM-Einträgen
(`data/hardware/hardware_compat_catalog.json`). Keine Installation, keine
Aktivierung, keine Downloads ausgeführt.

## 16. Raspberry-Pi-3-bis-5-Stand

Modellerkennung über Device-Tree (`raspberry_pi_detection.py`),
Bootmedium-Plan inkl. NVMe bei Pi 5 (`raspberry_pi_boot_plan.py`),
Kompatibilitäts-Zusammenfassung (`raspberry_pi_compatibility.py`) und
OS-Kandidatenmatrix (`raspberry_pi_os_plan.py`). Keine pauschale
"Pi 3-5 unterstützt"-Aussage; jede Board×Architektur×OS×Bootmedium-Kombination
einzeln bewertet. **Keine physischen Boards verfügbar** — nur
Device-Tree-Fixtures getestet.

## 17. 64-GB-Carrier-Entscheidung

Kapazitätsplan rechnet mit realen Bytes (`storage_facade`-Integration,
≥10 % Reserve). Strategieentscheidung: **Variante C (Orchestrator-Cache)**
als spezifikationsgemäßer Standard, da kein Beleg für einen validierten
gemeinsamen x86/Pi-Bootpfad existiert (`carrier_layout.py`,
`evaluate_carrier_strategy()`). Variante A bliebe möglich, sobald ein
Aufrufer echten Beleg liefert — aktuell nicht der Fall. **Keine
Partitionierung** durchgeführt.

## 18. OS-Katalog- und Provisionierungsstand

Katalog mit x86_64 (Debian/Ubuntu LTS/Mint) und ARM (Raspberry Pi OS/Debian
ARM64/Ubuntu Server ARM64) Einträgen, `download_enabled=false` erzwungen
(`data/provisioning/os_catalog.json` + `os_catalog.py`). Kompatibilitäts-
prüfung, SHA256-Verifikationsvorschau, Installationsplan-Vorschau mit
`write_allowed` **immer `false`** (`os_compatibility.py`,
`os_image_verifier.py`, `os_install_plan.py`). Kein Image-Download, kein
Schreibvorgang.

## 19. Telemetrie-/DCC-Anbindung

`hardware_inventory_summary_v1`-Contract mit strikter Allowlist-Validierung
(`hardware_telemetry_contract.py`) — Seriennummern/MAC/IP/volle EDID/
Hostnamen strukturell ausgeschlossen. Additive DCC-Statusfelder
(`hardware_dcc_status.py`) über `dcc_status_facade.py` und neuen
Dev-Dashboard-Endpunkt exponiert, bestehende DCC-Funktionen unverändert.

## 20. Tests mit exakten Ergebnissen

- **19 neue Testdateien**, zusammen **208 Tests, 1 skipped**, alle grün
  (Fixture-/Mock-basiert, keine reale Hardware, kein `/opt`, kein laufender
  Dienst berührt).
- Modul-Boundary-Guard (`check-module-boundaries.sh`, warn-only):
  ein durch diese Phase ausgelöster Hinweis
  (`hardware_new_logic_outside_discovery:mainboard_chipset_detection.py`)
  durch dokumentierenden Verweis auf die bewusste Parallelarchitektur
  behoben; verbleibende Hinweise sind vorbestehend und unabhängig von
  dieser Phase.
- Frontend-Typecheck (`tsc --noEmit`): **kein** durch diese Phase
  eingeführter Fehler (194 vorbestehende Fehler in unveränderten Dateien
  bleiben unangetastet — außerhalb des Scopes dieser Phase).
- Frontend-Build (`vite build`): **erfolgreich**.
- Vollständiger Backend-Testlauf (`backend/tests/`, 27 Dateien mit
  bekanntem, vorbestehendem `ModuleNotFoundError: httpx`-Umgebungsproblem
  ausgeschlossen — Details siehe unten): **3.450 passed, 12 failed → nach
  Fix des durch diese Phase ausgelösten Tile-Count-Tests: 11 verbleibende
  Fehler, alle verifiziert vorbestehend** (per `git stash`-Vergleich gegen
  den unveränderten Ausgangsstand bestätigt: `test_deploy_runner_rescue_
  storage_discovery_v1`, drei `test_pi_rs_payload_telemetry001_*`
  Dateiberechtigungs-/Permission-Probleme im Worktree, sechs
  httpx-abhängige `TestClient`-Importe in weiteren Dateien).
- `python3 backend/tools/check_version_consistency.py --repo-root .`:
  **ok=True**.

**Status:** `implemented_pending_runtime_deploy` für den vollständigen
Live-API-Nachweis (kein `./scripts/check-runtime-deploy-gate.sh`-Lauf in
dieser Phase — nicht erforderlich, da ausschließlich Fixture-/Mock-Tests
ohne `/opt`- oder Dienstzugriff verwendet wurden, siehe Phase-0-Gate-Regel).

## 21. Physisch getestete Hardware

**Keine.** Kein einziger Eintrag der physischen Testmatrix trägt den Status
`physically_verified`. Siehe
`docs/evidence/rescue/hardware-compat-001/PHYSICAL_HARDWARE_TEST_MATRIX.md`.

## 22. Nur simulierte oder Fixture-basierte Hardware

Alle 208 Tests der neuen Module basieren ausschließlich auf injizierten
Fixtures (`raw_text`, `sysfs_root`, `runner`-Callables). Dies betrifft
**alle** in dieser Phase behandelten Hardwareklassen (CPU/GPU/Mainboard/
USB/Input/Drucker/Scanner/Raspberry Pi 3-5/Carrier/OS-Katalog).

## 23. Blocker

Keine harten Blocker. Ein Umgebungs-Blocker (`ModuleNotFoundError: httpx`)
verhindert die vollständige Kollektion von 27 vorbestehenden Testdateien in
dieser lokalen Umgebung — unabhängig von dieser Phase, nicht behoben (kein
`pip install --break-system-packages` in geteilter Systemumgebung ohne
explizite Freigabe).

## 24. Warnungen

- Modul-Boundary-Guard bleibt insgesamt `review_required` (viele
  vorbestehende, phase-unabhängige Befunde zu `app.py`/`deploy_routes.py`-
  Größe, Frontend-Status-Mapping-Duplikaten usw. — außerhalb des Scopes
  dieser Phase, nicht verschlechtert).
- 194 vorbestehende TypeScript-Fehler in nicht von dieser Phase berührten
  Dateien (`tsc --noEmit`) — nicht neu, nicht behoben (außerhalb des
  Scopes).
- Frontend-Bundle-Größenwarnung (`index-*.js` > 500 kB) — vorbestehend,
  nicht durch diese Phase verursacht (neue Panels sind Teil des bestehenden
  Hauptbundles, kein Code-Splitting in dieser Phase eingeführt).
- 64-GB-Carrier-Strategie ist eine **Zwischenentscheidung** (Variante C)
  basierend auf fehlendem Gegenbeleg, keine endgültige, unveränderliche
  Produktentscheidung.

## 25. Nächster sinnvoller Schritt

`PI-RS-HW-ACTIVATE-002`: kontrollierte Live-Treiberaktivierung,
Offline-Firmwarecache, Drucker-/Scanner-Funktionstests, GPU-GUI-Bootprofile,
physische Raspberry-Pi-Tests, signierter Image-Download, kontrollierter
Betriebssystem-Write ausschließlich auf freigegebene Testmedien, Verify und
Bootnachweis — **nicht** Bestandteil dieser Phase.

## Endstatus

```
implemented_hardware_inventory_and_provisioning_preview_pending_physical_matrix
```

Dieser Status ist der in der Spezifikation als "erwarteter realistischer
Endstatus" benannte Wert. Es werden **keine** der unzulässigen Statuswerte
(`all_hardware_supported`, `raspberry_pi_3_to_5_verified`,
`printer_support_complete`, `gpu_support_complete`,
`universal_64gb_stick_verified`, `operating_system_installation_verified`,
`production_ready`) beansprucht.
