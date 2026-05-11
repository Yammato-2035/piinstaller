# Deploy Write Test Harness (DE)

## Ziel

Isolierter Test-Harness fuer spaetere Real-Write-Phasen, mit Schreiblogik nur auf erlaubten Testdateien.

## Sicherheitsrahmen

- keine Blockdevices
- keine /dev/*-Ziele
- kein Mount/Loop/Format/Partition
- nur regulaere Dateien unter erlaubten Testpfaden
- max_bytes hart begrenzt

## API

- `POST /api/deploy/write/harness/session`
- `POST /api/deploy/write/harness/execute`
