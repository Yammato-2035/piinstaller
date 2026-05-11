# Deploy Download/Cache Plan (DE)

## Ziel

Diese Phase plant nur, wie ein OS-Image spaeter sicher bezogen und lokal gecacht werden koennte.
Es werden keine Downloads ausgefuehrt und keine Daten geschrieben.

## Garantien

- kein Download
- kein Netzwerkzugriff
- keine Hashberechnung
- kein Entpacken/Mount/chroot
- kein Schreiben auf Zielplatten

## API

`POST /api/deploy/cache/plan`

Response enthaelt:

- `plan_status`
- `cache.cache_targets` (nur Kandidaten, keine Erstellung)
- `verification` (nur erwartete Parameter)
- `required_steps` (advisory, `auto_allowed=false`)
- `blocked_steps`, `risks`, `warnings`, `errors`
