# Deploy Cache Execute – Local-only (DE)

## Ziel

Diese Phase uebernimmt ausschliesslich lokale Image-Dateien in den Setuphelfer-Cache oder markiert sie als bereits bereit.

## Sicherheitsgrenzen

- kein Netzwerkzugriff
- kein Remote-Download
- kein Mount/Entpacken/chroot
- keine Zielplatten-Schreiboperation
- keine Installation

## API

- `POST /api/deploy/cache/session`
- `POST /api/deploy/cache/execute`

## Ablauf

1. Session + Token + TTL validieren
2. Source-Hash gegen Session pruefen
3. lokale Datei erneut validieren
4. optionale SHA256-Pruefung bei vorhandenem Hash
5. containment-sicher in erlaubten Cachepfad kopieren oder als ready markieren

## Hinweise

- Session ist single-use
- Remote-Quellen sind in dieser Phase blockiert
