# Raspberry Pi 3 bis 5 — Unterstützungsmodell

Stand: PI-RS-HW-COMPAT-PROVISION-001, Phase 19.

## Kernaussage

**Es gibt keine pauschale Aussage „Raspberry Pi 3–5 unterstützt".** Jede
Kombination aus Board, Architektur, Betriebssystem, Bootmedium und
Imageversion wird einzeln bewertet:

```
Board × Architektur × Betriebssystem × Bootmedium × Imageversion × Teststatus
```

Raspberry Pi 3 kann abweichende Architektur-, Speicher- und
Bootanforderungen gegenüber Raspberry Pi 5 haben.

## Abgedeckte Plattformfamilien

- Raspberry Pi 3 / 3B+
- Raspberry Pi 4
- Raspberry Pi 400
- Compute Module 4 (soweit generisch über Device-Tree erkennbar)
- Raspberry Pi 5
- Compute Module 5 (nur sofern im aktuellen Stack belastbar erkennbar)

## Module

| Modul | Zweck |
|---|---|
| `backend/platforms/raspberry_pi_detection.py` | Exakte Modellerkennung über `/proc/device-tree/model`, `/proc/device-tree/compatible`, SoC-Info, RAM-Größe |
| `backend/platforms/raspberry_pi_boot_plan.py` | Bootmedium-Unterstützung (microSD, USB-Massenspeicher, NVMe beim Pi 5, Netzwerkboot als `future/experimental`) |
| `backend/platforms/raspberry_pi_compatibility.py` | Kompatibilitäts-Zusammenfassung pro Modell |
| `backend/platforms/raspberry_pi_os_plan.py` | Matrix aus OS-Kandidaten je Modell/RAM/Architektur |

## Erkennungsquellen

- `/proc/device-tree/model`, `/proc/device-tree/compatible`
- SoC-Informationen und Architektur (`aarch64`/`armv7`)
- Bootmedium
- EEPROM-/Bootloaderstatus — **nur lesend**, keine Änderung
- RAM-Größe
- Netzwerkinterfaces, WLAN-/Bluetoothstatus
- USB-Controller, Storage, PCIe/NVMe (Pi 5)
- HAT-/Overlay-Informationen, soweit erkennbar
- Kamera-/Displayinterfaces — nur Erkennung, keine Aktivierung

## Statuswerte

- `boot_supported`
- `bootloader_update_recommended`
- `bootloader_update_required`
- `storage_supported`
- `os_compatible`
- `physical_validation_required`

## Betriebssystem-Matrix (Vorbereitung)

| Kategorie | Support-Status |
|---|---|
| Raspberry Pi OS | aktueller Katalogeintrag (siehe `data/provisioning/os_catalog.json`) |
| Debian ARM64 | aktueller Katalogeintrag |
| Ubuntu Server ARM64 | aktueller Katalogeintrag |
| Ubuntu Desktop ARM64 | optional |
| weitere Systeme | `future`/`unsupported` |

## Seriennummer/Datenschutz

Seriennummern werden **lokal nur redigiert** behandelt, nie im Klartext
übertragen. Für eine etwaige Gerätebindung wird ausschließlich ein stabiler,
gesalzener Hash verwendet — kein Rohwert.

## Keine EEPROM-Änderung in dieser Phase

Bootloader-/EEPROM-Status wird ausschließlich **gelesen**. Eine
EEPROM-Aktualisierung ist kein Bestandteil dieser Phase und bleibt
`PI-RS-HW-ACTIVATE-002` vorbehalten.

## Physischer Nachweis

Die aktuellen Module wurden gegen synthetische Device-Tree-Fixtures getestet
(`backend/tests/test_raspberry_pi_detection_v1.py`,
`test_raspberry_pi_os_compatibility_v1.py`). Ein physischer Testlauf gegen
reale Boards steht noch aus — siehe
`docs/evidence/rescue/hardware-compat-001/PHYSICAL_HARDWARE_TEST_MATRIX.md`.
Kein Modell darf ohne physischen Nachweis als „verifiziert" bezeichnet
werden.
