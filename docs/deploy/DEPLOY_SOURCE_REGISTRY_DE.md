# Deploy Source Registry (DE)

## Zweck

Die Deploy Source Registry verwaltet erlaubte Betriebssystemquellen nur als Metadaten und bewertet ihre Kompatibilitaet fuer spaetere Deploy-Phasen.

## Garantien dieser Phase

- kein Download
- kein Image-Schreiben
- kein Mount/Loop-Mount/chroot
- keine Installation
- keine Schreiboperationen auf Zielplatten

## API

- `GET /api/deploy/sources` liefert die Registry
- `POST /api/deploy/source/evaluate` liefert Kompatibilitaetsbewertung

## Registry-Typen

- `local_image`
- `remote_image` (nur Metadatenvalidierung, Download blockiert)
- `official_installer`

## Defensivregeln

- Architektur-/Plattform-Mismatch => inkompatibel
- blocked-Status => inkompatibel
- experimental => high risk markiert
- `remote_image` prueft nur URL/Checksum-Struktur (HTTPS, keine localhost/internal Hosts)
