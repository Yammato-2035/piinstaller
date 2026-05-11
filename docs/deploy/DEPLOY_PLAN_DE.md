# Deploy-Plan (ohne nutzbares Backup)

## Zweck

Der Deploy-Plan beantwortet **nur analytisch**, ob und unter welchen Bedingungen ein System **neu aufgesetzt** werden könnte (z. B. minimales Linux, Webserver-Rolle), **ohne** Installation, Partitionierung, Images oder Schreibzugriffe.

## API

`POST /api/deploy/plan`

Request-Body:

- `inspect_result`: Rohdaten aus Inspect (Phase 0/1)
- `safety_summary`: Write-Safety-Zusammenfassung
- `classification`: optional Phase-2-Klassifikation

Response:

- `code`: `DEPLOY_PLAN_OK` | `DEPLOY_PLAN_REVIEW_REQUIRED` | `DEPLOY_PLAN_BLOCKED` | `DEPLOY_PLAN_NOT_APPLICABLE`
- `plan`: strukturierter Plan (Profile, Schritte, Risiken, Blocker)
- `warnings` / `errors`: Listen von Codes

Die Folgephase ergänzt ein Execute-Prep-Contract (`/api/deploy/session`, `/api/deploy/execute`) als reinen NO-OP-Readiness-Check.

## Entscheidungsprinzipien

- Deploy nur plausibel bei **leerem** bzw. explizit leer signalisiertem Ziel oder `SAFETY_EMPTY_DISK` auf allen betrachteten Zielen.
- Block bei Windows, Dualboot, Systemplatte, Live-System, Safety-Fehler, unbekanntem Layout (Safety), nicht-leerem Datenträger.
- `review_required` bei unklaren Signalen (z. B. `unknown_layout`) oder gemischten Hinweisen.

## Profile und Schritte

Profile und `required_steps` sind **rein advisory**; `auto_allowed` ist immer `false`, Bestätigung ist vorgesehen.
