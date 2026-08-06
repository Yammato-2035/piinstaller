# Hardwarecompatibiliteitsmodel — Rescue Stick

Stand: PI-RS-HW-COMPAT-PROVISION-001 (Fase 19), uitgebreid met
PI-RS-HW-BASELINE-DIAG-I18N-002 (Fase 14).

Talen: [Deutsch](HARDWARE_COMPATIBILITY_MODEL_DE.md) ·
[English](HARDWARE_COMPATIBILITY_MODEL_EN.md) ·
[Français](HARDWARE_COMPATIBILITY_MODEL_FR.md) ·
[Nederlands](HARDWARE_COMPATIBILITY_MODEL_NL.md)

## Kernboodschap

**Detectie is geen garantie voor werking.** De reddingsstick toont voor elk
apparaat een navolgbare, meerledige status in plaats van een enkele
ja/nee-uitspraak.

## Statuslicht (Rescue-UI)

| Licht | Betekenis |
|---|---|
| 🟢 Groen | gedetecteerd, driver geladen, firmware aanwezig, apparaat bedrijfsklaar |
| 🟡 Geel | gedetecteerd, maar beperkt / optionele driver / fysieke test vereist / capaciteit niet volledig geverifieerd |
| 🔴 Rood | driver ontbreekt, firmware ontbreekt, kernel incompatibel, apparaat geblokkeerd, veilige activering niet mogelijk |
| ⚪ Grijs | onbekend, niet gecontroleerd, tool ontbreekt, geen betrouwbare classificatie |

Dit statuslicht is geïmplementeerd in `frontend/src/rescue/RescueHardwarePanel.tsx`
en `frontend/src/rescue/rescue-shell.css` (`.rescue-hw-badge-*`). Voor de
afzonderlijke hardware-basiscontrole (RAM/CPU/GPU/opslag) geldt een
vergelijkbaar, maar zelfstandig statuslicht — zie
`HARDWARE_BASELINE_DIAGNOSTICS_NL.md`.

## Gedekte hardwareklassen

1. CPU's en SoC's (`backend/core/cpu_platform_detection.py`)
2. GPU's/grafische paden (`backend/core/gpu_detection.py`, `gpu_driver_resolver.py`)
3. Moederborden en chipsets (`backend/core/mainboard_chipset_detection.py`)
4. PCI-/PCIe-apparaten (`backend/core/hardware_inventory.py::collect_pci_devices`)
5. USB-apparaten (`backend/core/usb_device_detection.py`)
6. Massaopslag/controllers (`hardware_inventory.py::collect_storage_controllers`)
7. Netwerkadapters (`hardware_inventory.py::collect_network_devices`)
8. Toetsenborden/muizen (`backend/core/input_device_detection.py`)
9. Printers (`backend/peripherals/printer_detection.py`)
10. Scanners (`backend/peripherals/scanner_detection.py`)
11. Raspberry Pi 3–5 (`backend/platforms/raspberry_pi_*.py`) — zie
    `RASPBERRY_PI_3_TO_5_SUPPORT_NL.md`
12. Voorbereiding multi-architectuurprovisionering — zie
    `MULTI_ARCH_PROVISIONING_MODEL_NL.md`

## Architectuurregel: geen hardgecodeerde massakatalogus

Er worden **geen** duizenden apparaten in de broncode vastgelegd. In
plaats daarvan:

```
Hardware-ID's/systeeminformatie
  → genormaliseerd HardwareDevice (backend/core/hardware_contracts.py)
  → generieke driver-/firmwareresolutie (backend/core/driver_resolver.py)
  → kleine, samengestelde compatibiliteitsdatabase voor bijzondere gevallen
    (data/hardware/hardware_compat_catalog.json)
  → veilige activeringsplanning (backend/core/driver_activation_plan.py, alleen preview)
  → navolgbare verificatie (evidence-referenties, fysieke testmatrix)
```

## Driver- en firmwareresolutie

De driver-/firmwareresolutie (`backend/core/driver_resolver.py`,
`backend/core/driver_activation_plan.py`) volgt voor elke gedetecteerde
apparaatklasse dezelfde volgorde:

1. driver die al aanwezig is in de actieve kernel/distributie
2. vrije, generieke driver uit de standaardrepository
3. samengesteld leverancierspakket (`data/hardware/hardware_compat_catalog.json`)
4. propriëtaire driver — uitsluitend als duidelijk gemarkeerde optie die
   handmatige bevestiging vereist (`driver_type: proprietary_optional`)
5. `unsupported`/`review_required` als geen van de bovenstaande niveaus van
   toepassing is

Firmware wordt volgens hetzelfde principe behandeld: aanwezigheid wordt
gedetecteerd en beoordeeld, afwezigheid wordt gemeld — een automatische
firmware-activering of automatische firmware-download vindt in deze
ontwikkelingsfase **niet** plaats. Elke activeringsplanning
(`driver_activation_plan.py`) is uitsluitend een preview (`preview-only`),
nooit een uitgevoerde schrijf- of installatieactie.

## Voorbeeld: multifunctioneel apparaat

Een "HP multifunctioneel apparaat" wordt gemodelleerd als **één apparaat
met meerdere capaciteiten**, niet als een algemene "werkt"-status:

```
Apparaat: HP multifunctioneel apparaat
Functies:
  - printer   → eigen operational_status
  - scanner   → eigen operational_status
  - storage_card_reader → eigen operational_status
```

Er wordt **nooit** beweerd dat de scanner werkt, alleen omdat de
printfunctie is gedetecteerd.

## Propriëtaire drivers

Propriëtaire drivers (bijv. de volledige NVIDIA-module) worden weergegeven
als een **optionele kandidaat** (`driver_type: proprietary_optional`),
nooit automatisch geïnstalleerd. Elke propriëtaire optie vereist een
afzonderlijke, handmatige beoordeling door de operator.

## Volgende fase

Daadwerkelijke driverinstallatie, firmware-activering,
printer-/scannerfunctietests en fysieke Raspberry Pi-boottests komen pas
aan bod in `PI-RS-HW-ACTIVATE-002`.
