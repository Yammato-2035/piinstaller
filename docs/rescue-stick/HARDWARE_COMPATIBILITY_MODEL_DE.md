# Hardware Compatibility Model — Rescue Stick

Stand: PI-RS-HW-COMPAT-PROVISION-001 (Phase 19), erweitert um
PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 14).

Sprachen: [Deutsch](HARDWARE_COMPATIBILITY_MODEL_DE.md) ·
[English](HARDWARE_COMPATIBILITY_MODEL_EN.md) ·
[Français](HARDWARE_COMPATIBILITY_MODEL_FR.md) ·
[Nederlands](HARDWARE_COMPATIBILITY_MODEL_NL.md)

## Kernaussage

**Erkennung ist keine Funktionsgarantie.** Der Rettungsstick zeigt für jedes
Gerät einen nachvollziehbaren, mehrstufigen Zustand statt einer einzelnen
Ja/Nein-Aussage.

## Statusampel (Rescue-UI)

| Ampel | Bedeutung |
|---|---|
| 🟢 Grün | erkannt, Treiber geladen, Firmware vorhanden, Gerät betriebsbereit |
| 🟡 Gelb | erkannt, aber eingeschränkt / optionaler Treiber / physischer Test erforderlich / Fähigkeit nicht vollständig verifiziert |
| 🔴 Rot | Treiber fehlt, Firmware fehlt, Kernel inkompatibel, Gerät blockiert, sichere Aktivierung nicht möglich |
| ⚪ Grau | unbekannt, nicht geprüft, Tool fehlt, keine belastbare Klassifikation |

Diese Ampeln sind in `frontend/src/rescue/RescueHardwarePanel.tsx` und
`frontend/src/rescue/rescue-shell.css` (`.rescue-hw-badge-*`) implementiert.
Für die separate Hardware-Baseline-Diagnostik (RAM/CPU/GPU/Datenträger) gilt
eine analoge, aber eigenständige Ampel — siehe
`HARDWARE_BASELINE_DIAGNOSTICS_DE.md`.

## Abgedeckte Hardwareklassen

1. CPUs und SoCs (`backend/core/cpu_platform_detection.py`)
2. GPUs/Grafikpfade (`backend/core/gpu_detection.py`, `gpu_driver_resolver.py`)
3. Mainboards und Chipsätze (`backend/core/mainboard_chipset_detection.py`)
4. PCI-/PCIe-Geräte (`backend/core/hardware_inventory.py::collect_pci_devices`)
5. USB-Geräte (`backend/core/usb_device_detection.py`)
6. Massenspeicher/Controller (`hardware_inventory.py::collect_storage_controllers`)
7. Netzwerkadapter (`hardware_inventory.py::collect_network_devices`)
8. Tastaturen/Mäuse (`backend/core/input_device_detection.py`)
9. Drucker (`backend/peripherals/printer_detection.py`)
10. Scanner (`backend/peripherals/scanner_detection.py`)
11. Raspberry Pi 3–5 (`backend/platforms/raspberry_pi_*.py`) — siehe
    `RASPBERRY_PI_3_TO_5_SUPPORT_DE.md`
12. Multi-Arch-Provisionierungsvorbereitung — siehe
    `MULTI_ARCH_PROVISIONING_MODEL_DE.md`

## Architekturregel: kein hartcodierter Massenkatalog

Es werden **nicht** tausende Geräte im Quellcode eingetragen. Stattdessen:

```
Hardware-IDs/Systeminformationen
  → normalisiertes HardwareDevice (backend/core/hardware_contracts.py)
  → generische Treiber-/Firmwareauflösung (backend/core/driver_resolver.py)
  → kleine kuratierte Kompatibilitätsdatenbank für Sonderfälle
    (data/hardware/hardware_compat_catalog.json)
  → sichere Aktivierungsplanung (backend/core/driver_activation_plan.py, preview-only)
  → nachvollziehbare Verifikation (Evidence-Referenzen, physische Testmatrix)
```

## Treiber- und Firmwareauflösung

Die Treiber-/Firmwareauflösung (`backend/core/driver_resolver.py`,
`backend/core/driver_activation_plan.py`) folgt für jede erkannte
Geräteklasse derselben Reihenfolge:

1. bereits im laufenden Kernel/Distribution vorhandener Treiber
2. freier, generischer Treiber aus dem Standardrepository
3. kuratiertes Herstellerpaket (`data/hardware/hardware_compat_catalog.json`)
4. proprietärer Treiber — ausschließlich als klar gekennzeichnete,
   manuell zu bestätigende Option (`driver_type: proprietary_optional`)
5. `unsupported`/`review_required`, wenn keine der obigen Stufen zutrifft

Firmware wird nach demselben Prinzip behandelt: Vorhandensein wird erkannt
und bewertet, ein Fehlen wird gemeldet — eine automatische
Firmware-Aktivierung oder ein automatischer Firmware-Download findet in
dieser Entwicklungsphase **nicht** statt. Jede Aktivierungsplanung
(`driver_activation_plan.py`) ist ausschließlich eine Vorschau
(`preview-only`), niemals ein ausgeführter Schreib- oder
Installationsvorgang.

## Beispiel: Multifunktionsgerät

Ein „HP Multifunktionsgerät" wird als **ein Gerät mit mehreren Capabilities**
modelliert, nicht als ein pauschaler „funktioniert"-Status:

```
Gerät: HP Multifunktionsgerät
Funktionen:
  - printer   → eigener operational_status
  - scanner   → eigener operational_status
  - storage_card_reader → eigener operational_status
```

Es wird **nie** behauptet, der Scanner funktioniere, nur weil die
Druckfunktion erkannt wurde.

## Proprietäre Treiber

Proprietäre Treiber (z. B. NVIDIA-Vollmodul) werden als **optionaler
Kandidat** (`driver_type: proprietary_optional`) dargestellt, niemals
automatisch installiert. Jede proprietäre Option erfordert eine gesonderte,
manuelle Prüfung durch den Operator.

## Nächste Phase

Reale Treiberinstallation, Firmwareaktivierung, Drucker-/Scanner-Funktionstests
und physische Raspberry-Pi-Boot-Tests folgen erst in
`PI-RS-HW-ACTIVATE-002`.
