# 64-GB-Carrier-Architektur — Rescue Stick

Stand: PI-RS-HW-COMPAT-PROVISION-001 (Phase 19), erweitert um
PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 14).

Sprachen: [Deutsch](64GB_CARRIER_ARCHITECTURE_DE.md) · [English](64GB_CARRIER_ARCHITECTURE_EN.md) · [Français](64GB_CARRIER_ARCHITECTURE_FR.md) · [Nederlands](64GB_CARRIER_ARCHITECTURE_NL.md)

## Kernaussage

**Ein einzelner 64-GB-Stick kann nicht unbegrenzt vollständige
Betriebssystemimages enthalten.** Setuphelfer verwendet deshalb einen
Katalog, einen begrenzten Cache und signierte Images statt eines
„Alles-drauf"-Ansatzes.

## Verglichene Varianten (`backend/rescue/carrier_layout.py`)

| Variante | Beschreibung | Voraussetzung |
|---|---|---|
| **A — Universal** | Ein Stick bootet nativ sowohl x86_64 als auch Raspberry Pi | belegter, validierter gemeinsamer Bootpfad (existiert aktuell **nicht**) |
| **B — Split Carriers** | Gemeinsamer Build-Katalog, aber getrennte x86- und ARM/Pi-Carrier | zwei physische Sticks nötig |
| **C — Orchestrator Cache** | Universal-Rescue-/Orchestrator-Stick mit herunterladbaren/zwischengespeicherten Zielimages | Standard, falls kein Universal-Bootpfad belegt ist |

### Entscheidung

Da in diesem Repository **kein Beleg** für einen validierten gemeinsamen
Boot-Sektor/ESP-Pfad für x86_64 (BIOS/UEFI) **und** Raspberry-Pi-SD-/EEPROM-Boot
vorliegt, ist **Variante C (Orchestrator-Cache)** die spezifikationsgemäße
Standardannahme. `evaluate_carrier_strategy()` markiert Variante A
ausschließlich als `decided`, wenn ein Aufrufer explizit
`universal_boot_path_evidence=True` mit tatsächlichem Beleg übergibt.

Dies ist eine evidenzbasierte Zwischenstandsdokumentation — keine endgültige
Produktentscheidung.

## Kapazitätsplan (`backend/rescue/carrier_capacity_planner.py`)

Der Plan rechnet **mit tatsächlichen Bytes des Mediums**, nicht mit einer
pauschalen 64-GB-Annahme. Es wird eine Sicherheitsreserve von **mindestens
10 %** eingeplant. Reale Byte-Ermittlung erfolgt über die bestehende
`storage_facade` — keine eigene `lsblk`-Logik.

## Möglicher Carrier-Inhalt (`backend/rescue/carrier_content_catalog.py`)

- Setuphelfer Rescue Runtime
- x86_64-Bootpfad
- optionale ARM-/Pi-Bootassets, sofern validiert
- Hardwarekatalog (`data/hardware/`)
- Treiber-/Firmware-Offlinepakete
- Imagekatalog (`data/provisioning/os_catalog.json`)
- begrenzter Imagecache
- Evidence-/Logbereich
- Update- und Signaturmetadaten

## Nicht-Ziel dieser Phase

**Keine Partitionierung.** `carrier_layout.py` und
`carrier_capacity_planner.py` erzeugen ausschließlich Pläne/Bewertungen,
keine Schreibvorgänge auf reale Medien.
