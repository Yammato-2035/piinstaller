# Deploy Write Plan (DE)

## Ziel

Simulation eines spaeteren Deploy-Schreibvorgangs auf ein Zielgeraet, ohne echte Datentraeger-Schreiboperation.

## Eigenschaften

- reiner Plan/Simulation
- erneute Safety-Gates
- nur Codes in Responses
- alle simulierten Schritte mit `auto_allowed=false`

## Hard-Blocks

- Ziel fehlt / Session-Mismatch
- Systemdisk, Live-System
- Windows, Dualboot
- Unknown Device
- Ziel nicht leer
- ungueltiges Image-Inspect-Ergebnis

## Wichtiger Hinweis

Diese Phase fuehrt kein Schreiben, keine Partitionierung, kein Formatieren und kein Image-Write aus.
