# Knowledge Base: Inspect Phase 0/1 (DE)

## Defensive Analyse

Inspect Phase 0/1 dient als defensive Analyseebene fuer spaetere Rescue-/Deploy-Pfade.
Der Fokus liegt auf stabiler Datenerhebung und reproduzierbaren Codes.

## Keine Schreiboperationen

- keine Mount-/Repair-Schreibzugriffe
- keine Restore-Aktionen
- keine Deploy-Aktionen
- keine Veraenderung von Partitionstabellen

## Datenquellen

- `modules.storage_detection.*`
- `modules.inspect_storage.*`
- `modules.inspect_boot.analyze_boot_status`
- `modules.rescue_readonly_analyze._analyze_network`

## Vorbereitung fuer Rescue/Deploy

Inspect liefert vorbereitende Rohdaten und Hinweis-Flags (`capabilities.os_hints`), aber keine Freigabeentscheidungen.
Freigaben bleiben in spaeteren Phasen mit expliziten Sicherheitsgates.
