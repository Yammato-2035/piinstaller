# Developer Dashboard — FAQ

## Warum war der Roadmap-Bereich nicht sichtbar?

Oft wurde das **Governance-Cockpit** (`CockpitApp`) genutzt statt der Seite **Developer Dashboard** (`dev-dashboard`). Das Cockpit hatte bis 2026-05-27 nur die Governance-Matrix, keinen Roadmap-Registry-Block. Die API lieferte Roadmap-Daten trotzdem.

## Welche Quelle nutzt der Roadmap-Bereich?

- Live: Backend-Registry (`/api/dev-dashboard/roadmap`, eingebettet in `/status`)
- Offline: Snapshot oder STATUS_MATRIX-Ableitung (mit Hinweis „Offline/Snapshot“)

## Was bedeutet Offline-/Snapshot-Roadmap?

Teilweise Einträge aus der Ampel-Matrix — **kein** vollständiges Meilenstein-Bundle. Kein Fake-Green.

## Warum werden rote Blocker weiterhin angezeigt?

Release-Gate, Backup, Rescue und Packaging bleiben rot/gelb ohne Evidence — absichtlich.

## Warum erscheint „grün“ nur mit Evidence?

Die Sektion **Bereit / stabil** und OK-Badges beziehen sich nur auf Gates mit `passed=true` bzw. `deploy_drift.status=green`. Farben ändern keine Backend-Logik.
