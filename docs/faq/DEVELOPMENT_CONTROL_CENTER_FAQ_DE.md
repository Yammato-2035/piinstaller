# FAQ — Development Control Center (DE)

## Wo ist die Roadmap?

Tab **Roadmap** im Development Control Center. Daten kommen aus `/api/dev-dashboard/roadmap`.

## Warum ist SSH rot/grau?

SSH **disabled** ist im Lab-MVP **gewollt** und wird als sicherer Zustand (grün) angezeigt, nicht als Fehler.

## Warum keine Public Uploads?

Public Rescue Auto-Upload bleibt blockiert. **Disabled** ist korrekt.

## Was ist der Telemetrieserver?

Der **Development Server** (`local_lab`) — ingest-only, read-only SSH vorbereitet aber deaktiviert.

## Kann ich von hier ein ISO bauen?

Nein. ISO-Build-Status bleibt **pending** bis echte Build-Evidence existiert.

## Sind die Doku-Zahlen live?

Read-only Scan von `docs/` — keine manuellen Hardcodes.
