# Deploy Image Inspect (DE)

## Ziel

Read-only Vorpruefung eines lokal gecachten Images vor spaeterer Deploy-Freigabe.

## Erlaubte Pruefungen

- Datei existiert
- regulaere Datei
- Pfad unter erlaubtem Setuphelfer-Cache
- Endung (.img/.iso/.qcow2)
- Dateigroesse > 0
- optionale SHA256-Pruefung bei gesetzter expected_checksum

## Nicht erlaubt

- kein Mount/Loop-Device
- kein Entpacken
- keine Partitionsanalyse
- keine Inhaltsanalyse im Image
- keine Installation
