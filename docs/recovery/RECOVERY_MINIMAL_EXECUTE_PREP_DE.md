# Recovery Minimal Execute Prep (DE)

## Ziel
Bereitet Session- und Execute-Contract für spätere Recovery-Ausführung vor.
In dieser Phase werden keine Schritte tatsächlich ausgeführt.

## API
- `POST /api/recovery/minimal/session`
- `POST /api/recovery/minimal/execute`

## Verhalten
- Session + Token + Plan-Hash-Bindung
- Ablaufzeit und Target-Prüfung
- Execute liefert nur `RECOVERY_MINIMAL_EXECUTE_READY`
- Keine Systemänderung
