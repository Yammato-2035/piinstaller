# Raspberry Pi 3 tot 5 — Ondersteuningsmodel

Stand: PI-RS-HW-COMPAT-PROVISION-001 (Fase 19), uitgebreid met
PI-RS-HW-BASELINE-DIAG-I18N-002 (Fase 14).

Talen: [Deutsch](RASPBERRY_PI_3_TO_5_SUPPORT_DE.md) ·
[English](RASPBERRY_PI_3_TO_5_SUPPORT_EN.md) ·
[Français](RASPBERRY_PI_3_TO_5_SUPPORT_FR.md) ·
[Nederlands](RASPBERRY_PI_3_TO_5_SUPPORT_NL.md)

## Kernboodschap

**Er bestaat geen algemene uitspraak "Raspberry Pi 3–5 ondersteund".**
Elke combinatie van board, architectuur, besturingssysteem, bootmedium en
image-versie wordt afzonderlijk beoordeeld:

```
Board × architectuur × besturingssysteem × bootmedium × image-versie × teststatus
```

Raspberry Pi 3 kan afwijkende architectuur-, geheugen- en bootvereisten
hebben ten opzichte van Raspberry Pi 5.

## Gedekte platformfamilies

- Raspberry Pi 3 / 3B+
- Raspberry Pi 4
- Raspberry Pi 400
- Compute Module 4 (voor zover generiek herkenbaar via device tree)
- Raspberry Pi 5
- Compute Module 5 (alleen indien betrouwbaar herkenbaar in de huidige
  stack)

## Modules

| Module | Doel |
|---|---|
| `backend/platforms/raspberry_pi_detection.py` | Exacte modelherkenning via `/proc/device-tree/model`, `/proc/device-tree/compatible`, SoC-info, RAM-grootte |
| `backend/platforms/raspberry_pi_boot_plan.py` | Ondersteuning bootmedium (microSD, USB-massaopslag, NVMe bij Pi 5, netwerkboot als `future/experimental`) |
| `backend/platforms/raspberry_pi_compatibility.py` | Compatibiliteitsoverzicht per model |
| `backend/platforms/raspberry_pi_os_plan.py` | Matrix van OS-kandidaten per model/RAM/architectuur |

## Detectiebronnen

- `/proc/device-tree/model`, `/proc/device-tree/compatible`
- SoC-informatie en architectuur (`aarch64`/`armv7`)
- Bootmedium
- EEPROM-/bootloaderstatus — **alleen-lezen**, geen wijziging
- RAM-grootte
- Netwerkinterfaces, wifi-/bluetoothstatus
- USB-controllers, opslag, PCIe/NVMe (Pi 5)
- HAT-/overlay-informatie, indien herkenbaar
- Camera-/schermInterfaces — alleen detectie, geen activering

## Statuswaarden

- `boot_supported`
- `bootloader_update_recommended`
- `bootloader_update_required`
- `storage_supported`
- `os_compatible`
- `physical_validation_required`

## Besturingssysteemmatrix (voorbereiding)

| Categorie | Supportstatus |
|---|---|
| Raspberry Pi OS | huidige catalogusvermelding (zie `data/provisioning/os_catalog.json`) |
| Debian ARM64 | huidige catalogusvermelding |
| Ubuntu Server ARM64 | huidige catalogusvermelding |
| Ubuntu Desktop ARM64 | optioneel |
| overige systemen | `future`/`unsupported` |

## Serienummer/privacy

Serienummers worden **lokaal alleen geredigeerd** behandeld, nooit in
platte tekst verzonden. Voor een eventuele apparaatbinding wordt
uitsluitend een stabiele, gesalte hash gebruikt — nooit een ruwe waarde.

## Geen EEPROM-wijziging in deze fase

De bootloader-/EEPROM-status wordt uitsluitend **gelezen**. Een
EEPROM-update maakt geen deel uit van deze fase en blijft voorbehouden aan
`PI-RS-HW-ACTIVATE-002`.

## Fysiek bewijs

De huidige modules zijn getest tegen synthetische device-tree-fixtures
(`backend/tests/test_raspberry_pi_detection_v1.py`,
`test_raspberry_pi_os_compatibility_v1.py`). Een fysieke testrun tegen
echte boards ontbreekt nog — zie
`docs/evidence/rescue/hardware-compat-001/PHYSICAL_HARDWARE_TEST_MATRIX.md`.
Geen enkel model mag zonder fysiek bewijs als "geverifieerd" worden
aangeduid.
