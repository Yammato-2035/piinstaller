# 64-GB-Carrier-Architektur — Rescue Stick

Stand: PI-RS-HW-COMPAT-PROVISION-001, Phase 19.

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

Da in diesem Repository **kein Beleg** für einen validierten,
gemeinsamen Boot-Sektor/ESP-Pfad für x86_64 (BIOS/UEFI) **und**
Raspberry-Pi-SD-/EEPROM-Boot vorliegt, ist **Variante C
(Orchestrator-Cache)** die spezifikationsgemäße Standardannahme dieser
Phase. `evaluate_carrier_strategy()` markiert Variante A ausschließlich als
`decided`, wenn ein Aufrufer explizit `universal_boot_path_evidence=True`
mit tatsächlichem Beleg übergibt — es wird **nichts angenommen**.

Dies ist eine **Phase-19-Dokumentation eines bereits in Phase 12 gefällten,
evidenzbasierten Zwischenstands** — keine endgültige Produktentscheidung.
Ein Wechsel zu Variante A wäre jederzeit möglich, sobald ein validierter
Universal-Bootpfad nachgewiesen ist.

## Kapazitätsplan (`backend/rescue/carrier_capacity_planner.py`)

Der Plan rechnet **mit tatsächlichen Bytes des Mediums**, nicht mit einer
pauschalen 64-GB-Annahme:

```json
{
  "carrier_size_bytes": 0,
  "layout_status": "ok|review_required|blocked",
  "runtime_bytes": 0,
  "driver_cache_bytes": 0,
  "image_cache_bytes": 0,
  "evidence_bytes": 0,
  "reserved_bytes": 0,
  "max_cached_images": 0,
  "recommended_strategy": "universal|split_carriers|orchestrator_cache",
  "warnings": []
}
```

Es wird eine Sicherheitsreserve von **mindestens 10 %** (oder eine
projektspezifisch begründete größere Reserve) eingeplant. Reale
Byte-Ermittlung erfolgt über die bestehende `storage_facade`
(`get_block_device_size_bytes`) — es wird **keine** eigene `lsblk`-Logik
neu implementiert.

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
