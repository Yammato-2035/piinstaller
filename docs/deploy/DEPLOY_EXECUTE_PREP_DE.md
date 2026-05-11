# Deploy Execute Prep (DE)

## Ziel

Diese Phase erstellt nur die kontrollierte **Session- und Execute-Vertragsstruktur** fuer spaetere Deploy-Schritte.
Es werden **keine** Installationen, **keine** Partitionierung und **keine** Systemaenderungen ausgefuehrt.

## Endpunkte

- `POST /api/deploy/session`
- `POST /api/deploy/execute`

## Session-Regeln

- `plan_status` muss `ok` sein
- `blocked_steps` muss leer sein
- `selected_profile` muss im Plan enthalten und `suitable=true` sein
- `selected_profile.auto_allowed` muss `false` sein
- alle `required_steps.auto_allowed` muessen `false` sein
- Session bindet `target_device`, `selected_profile`, Token und Plan-Hash
- Session ist zeitlich begrenzt (TTL)

## Execute in dieser Phase

`/api/deploy/execute` prueft nur:

- Session vorhanden
- Token korrekt
- Session nicht abgelaufen
- `target_device` passt zur Session
- `selected_profile` passt zur Session
- optionaler Plan-Hash passt

Dann wird **nur** `DEPLOY_EXECUTE_READY` geliefert (`next_phase = deploy_preview`).
Es gibt keine Installations- oder Schreibaktion.
