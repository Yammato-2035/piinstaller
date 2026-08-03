# Hardware Detection Architecture — PI-RS-HW-COMPAT-PROVISION-001

Stand: Phase 19. Beschreibt die neue, parallele Hardware-Erkennungsschicht des
Rettungssticks. Ersetzt **keine** bestehende Logik der Produkt-App
(`backend/core/hardware_discovery.py`) oder des groben Rescue-Assessments
(`backend/core/rescue_system_assessment_v2.py`) — siehe
`docs/evidence/rescue/hardware-compat-001/HARDWARE_DISCOVERY_IST_AUDIT.md` für
die vollständige Abgrenzung.

## Leitprinzip

> **„Erkannt" ist nicht gleich „betriebsbereit".**

Ein Gerät durchläuft mehrere unabhängige Zustände, die getrennt bewertet
werden müssen (Beispiel NVIDIA-GPU):

```
PCI-Gerät erkannt
      │
      ▼
passender Treiber bekannt (Kandidat)
      │
      ▼
Treiber im System vorhanden
      │
      ▼
Kernelmodul geladen
      │
      ▼
DRM-Gerät erzeugt
      │
      ▼
Displayausgabe funktioniert  ← nur durch physischen Test verifizierbar
```

Jede Stufe wird in `backend/core/hardware_contracts.py` als eigenes Feld auf
`HardwareDevice` bzw. `HardwareDriverState`/`HardwareFirmwareState` abgebildet,
niemals als einzelnes Bool „funktioniert".

## Datenfluss

```
Rohquellen (sysfs, /proc, lspci, lsusb, dmidecode, lsmod, modinfo, dmesg, ...)
      │  (read-only, Tool-Fehlen = capability_missing, kein Crash)
      ▼
backend/core/hardware_inventory.py
  collect_pci_devices / collect_usb_devices / collect_platform_devices /
  collect_input_devices / collect_network_devices /
  collect_storage_controllers / collect_kernel_driver_state /
  collect_firmware_errors
      │
      ▼
Klassenspezifische Detektoren (konsumieren Inventory-Rohdaten, fügen
Domänenwissen hinzu, duplizieren kein Parsing):
  - backend/core/cpu_platform_detection.py
  - backend/core/mainboard_chipset_detection.py
  - backend/core/gpu_detection.py
  - backend/core/usb_device_detection.py
  - backend/core/input_device_detection.py
  - backend/peripherals/printer_detection.py
  - backend/peripherals/scanner_detection.py
  - backend/platforms/raspberry_pi_detection.py
      │
      ▼
backend/core/hardware_compat_catalog.py
  (kuratierte Sonderfälle, siehe data/hardware/hardware_compat_catalog.json)
      │
      ▼
Treiber-/Firmware-Resolver (siehe DRIVER_FIRMWARE_RESOLUTION_ARCHITECTURE.md)
      │
      ▼
Read-only API-Routen (backend/api/routes/rescue_hardware.py, rescue_peripherals.py,
  rescue_platform.py)
      │
      ▼
Rescue-UI (frontend/src/rescue/RescueHardwarePanel.tsx)
      │
      ▼
Telemetrie-Redaction (backend/core/hardware_telemetry_contract.py) — nur
  aggregierte, redigierte Werte verlassen das Gerät
```

## Zentrales Vokabular (`hardware_contracts.py`)

| Contract | Zweck |
|---|---|
| `HardwareInventory` | Container für alle erkannten `HardwareDevice`-Einträge eines Laufs |
| `HardwareDevice` | Ein physisches/logisches Gerät mit Bus, IDs, Treiber-/Firmwarestatus, Capabilities, Issues, Empfehlungen, Evidence, Privacy-Flags |
| `HardwareDriverState` | Gebundener Treiber, Kandidaten, geladene Kernelmodule getrennt vom Gerät selbst |
| `HardwareFirmwareState` | `present\|missing\|unknown\|not_required` getrennt vom Treiberstatus |
| `HardwareCapability` | Einzelne Fähigkeit eines Geräts (z. B. bei Multifunktionsgeräten: `printer`, `scanner`) mit eigenem Betriebsstatus |
| `HardwareIssue` | Strukturierter, code-basierter Befund (kein Freitext-Fehler) |
| `HardwareRecommendation` | Nächster sinnvoller Schritt, keine automatische Aktion |
| `HardwareEvidenceReference` | Pfad/Referenz auf Beleg (Log, Screenshot, Katalogeintrag) |
| `PlatformIdentity` | Plattformklasse (x86_64-Desktop, Laptop, Raspberry-Pi-Modell, …) |
| `PeripheralCapability` | Peripherie-Fähigkeit (Drucker/Scanner-Funktion) mit eigenem Status |

Stabile `operational_status`-Werte: `detected`, `identified`, `driver_available`,
`driver_loaded`, `firmware_present`, `firmware_missing`, `ready`, `limited`,
`blocked`, `unsupported`, `unknown`, `review_required`.

## Nicht-Ziele dieser Phase

Diese Architektur beschreibt ausschließlich **Erkennung, Klassifikation und
Planvorschau**. Es findet keine Treiberinstallation, keine
Firmwareaktivierung, kein Schreibvorgang und keine automatische
Modulaktivierung statt. Siehe `PI-RS-HW-ACTIVATE-002` (nächster Meilenstein)
für die kontrollierte Aktivierungsphase.

## Testbarkeit

Jedes Detektionsmodul akzeptiert injizierbare Abhängigkeiten
(`runner`-Callable für Subprozesse, `sysfs_root` für Dateisystemzugriff,
`raw_text`-Parameter für Kommandoausgaben), damit Unit-Tests ohne reale
Hardware oder installierte Tools laufen können. Siehe
`backend/tests/test_hardware_*_v1.py` und
`docs/evidence/rescue/hardware-compat-001/PHYSICAL_HARDWARE_TEST_MATRIX.md`
für den Unterschied zwischen Fixture-Test und physischer Verifikation.
