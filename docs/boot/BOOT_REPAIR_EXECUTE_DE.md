# Boot Repair Execute (DE)

## Ziel
Einzelne, minimale Boot-Reparaturen aus einer validierten Repair-Session ausführen.
Kein Fix-All, keine Kaskade, keine automatischen Folgeaktionen.

## Sicherheitsregeln
- Token-pflichtig
- Session mit Ablaufzeit
- exakt eine Action pro Session
- Windows/Dualboot blockiert
- High-Risk blockiert
- Post-Check via Boot Capability

## API
- `POST /api/boot/repair/session`
- `POST /api/boot/repair/execute`

Nur für klar erlaubte Aktionen in Phase 2.
