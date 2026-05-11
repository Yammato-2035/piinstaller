# Deploy Write Execute Dry-Run (DE)

## Ziel

Finale Dry-Run-Vertragsphase fuer Deploy-Write mit Session/Token/Confirmation-Bindung und Re-Checks direkt vor der simulierten Ausfuehrung.

## Garantien

- kein Schreiben auf Datentraeger
- kein Partitionieren/Formatieren
- kein Mount/Loop/Chroot
- nur simulierte Step-Ausgabe

## API

- `POST /api/deploy/write/session`
- `POST /api/deploy/write/execute`

Beide Endpunkte sind fail-closed und liefern nur Code-basierte Antworten.
