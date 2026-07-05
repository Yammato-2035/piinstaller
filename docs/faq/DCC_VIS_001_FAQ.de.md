# FAQ — DCC-VIS-001 (de)

## Warum ist das DCC rot?

Meist: Runtime Gate (Phase 0) nicht grün, fehlender Developer Token, oder Standalone-Modus. Rot bedeutet nicht automatisch „Backend tot“.

## Warum ist die API erreichbar, aber Runtime Gate blockiert?

`/api/version` prüft nur den lokalen Backend-Prozess. Das Runtime Gate prüft zusätzlich Deploy-Drift, `/opt`-Stand und Dienst-Status.

## Was bedeutet Developer Token?

Header `X-Setuphelfer-Developer-Token` für Dev-Dashboard-Routen. Wird lokal im Browser gespeichert — nie in Git.

## Warum sind Backup/Restore/Deploy gesperrt?

DCC bleibt read-only solange Runtime-Gates rot sind (Hard-Safety).

## Was bedeutet sichtbarer Changelog?

Abgeschlossene Phasen (z. B. TEL-011) mit Ergebnis, Workspace und Sichtbarkeit pro Oberfläche.

## Wann Workspace wechseln?

Wenn die nächste Phase in einem anderen Repo liegt (z. B. TEL-012 → Telemetry Server).

## Warum TEL-011 abgeschlossen, aber DCC nicht grün?

Technisch abgeschlossen im Telemetry Server; DCC-Sichtbarkeit war vor DCC-VIS-001 noch nicht angebunden.
