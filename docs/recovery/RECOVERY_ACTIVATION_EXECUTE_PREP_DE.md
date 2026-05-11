# Recovery Activation Execute Prep (DE)

## Ziel
Session- und Execute-Vertrag für spätere kontrollierte Aktivierung vorbereiten.

## In dieser Phase
- keine SSH-Aktivierung
- kein Benutzer anlegen
- kein Dienststart
- keine Portöffnung
- keine Netzwerk-/Firewall-Änderung

## API
- `POST /api/recovery/activation/session`
- `POST /api/recovery/activation/execute` (NO-OP READY)
