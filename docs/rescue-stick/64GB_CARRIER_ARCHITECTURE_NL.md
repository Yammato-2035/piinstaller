# 64-GB-carrierarchitectuur — Rescue Stick

Status: PI-RS-HW-COMPAT-PROVISION-001 (Phase 19), uitgebreid met
PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 14).

Talen: [Deutsch](64GB_CARRIER_ARCHITECTURE_DE.md) · [English](64GB_CARRIER_ARCHITECTURE_EN.md) · [Français](64GB_CARRIER_ARCHITECTURE_FR.md) · [Nederlands](64GB_CARRIER_ARCHITECTURE_NL.md)

## Kernboodschap

**Eén enkele 64-GB-stick kan niet onbeperkt volledige besturingssysteemimages
bevatten.** Setuphelfer gebruikt daarom een catalogus, een begrensde cache en
ondertekende images in plaats van een „alles-erop"-aanpak.

## Vergelijkte varianten (`backend/rescue/carrier_layout.py`)

| Variant | Beschrijving | Voorwaarde |
|---|---|---|
| **A — Universal** | Eén stick boot natively voor x86_64 én Raspberry Pi | bewezen, gevalideerd gedeeld bootpad (bestaat momenteel **niet**) |
| **B — Split Carriers** | Gedeelde buildcatalogus, maar aparte x86- en ARM/Pi-carriers | twee fysieke sticks nodig |
| **C — Orchestrator Cache** | Universele rescue-/orchestratorstick met downloadbare/gecachete doelimages | standaard wanneer geen universeel bootpad is bewezen |

### Beslissing

Omdat deze repository **geen bewijs** heeft voor een gevalideerd gedeeld
bootsector/ESP-pad voor x86_64 (BIOS/UEFI) **én** Raspberry Pi SD-/EEPROM-boot,
is **variant C (orchestrator cache)** de specificatieconforme standaard.
`evaluate_carrier_strategy()` markeert variant A alleen als `decided` wanneer
een aanroeper expliciet `universal_boot_path_evidence=True` met echt bewijs
doorgeeft.

Dit is evidence-gebaseerde tussendocumentatie — geen definitieve
productbeslissing.

## Capaciteitsplan (`backend/rescue/carrier_capacity_planner.py`)

Het plan rekent met **werkelijke bytes van het medium**, niet met een
forfaitaire 64-GB-aanname. Er wordt een veiligheidsreserve van **minstens
10 %** gepland. Werkelijke bytedetectie hergebruikt `storage_facade` — geen
nieuwe `lsblk`-logica.

## Mogelijke carrierinhoud (`backend/rescue/carrier_content_catalog.py`)

- Setuphelfer Rescue Runtime
- x86_64-bootpad
- optionele ARM-/Pi-bootassets indien gevalideerd
- hardwarecatalogus (`data/hardware/`)
- offline driver-/firmwarepakketten
- imagecatalogus (`data/provisioning/os_catalog.json`)
- begrensde imagecache
- evidence-/loggebied
- update- en handtekeningmetagegevens

## Niet-doel van deze fase

**Geen partitionering.** `carrier_layout.py` en
`carrier_capacity_planner.py` maken uitsluitend plannen/beoordelingen —
geen schrijfacties naar echte media.
