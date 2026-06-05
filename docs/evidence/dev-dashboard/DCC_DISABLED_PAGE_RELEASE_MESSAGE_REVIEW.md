# DCC Disabled Page — Release Message Review

**Datum:** 2026-06-05  
**Komponente:** `frontend/src/pages/ExternalDevelopmentControlCenter.tsx` (`DevControlDisabledPage`)

## Status

**`review_required`**

## Warum?

Positiv (fachlich klar, nicht Port-/Backend-Fehler):

1. Explizite Klarstellung „Dies ist kein Portfehler.“
2. Port-Orientierung: Backend `127.0.0.1:8000`, Cockpit `127.0.0.1:3001`, nginx `127.0.0.1:8080 — nicht SetupHelfer-DCC`.
3. Keine Buttons zum Umschalten: Die Seite wird direkt gerendert und gibt keinen Wechsel-CTA aus.
4. Docs-Hinweis vorhanden: `docs/dev-dashboard/PORTS_AND_PROFILES.md`.

Review-Punkte (nicht vollständig im Sinne des neuen Gate-Texts):

1. Die Seite zeigt nicht explizit `dev_control_enabled` als Feld an.
2. Der Operator-Hinweis „local_lab nur manuell/mit sudo aktivieren, nicht aus der UI“ ist im Text nicht enthalten.
3. DCC-URL (Cockpit URL mit `/?window=cockpit`) wird nicht als eigenes Element hervorgehoben (nur Ports-Liste).

## Referenz (Code)

`DevControlDisabledPage` enthält u. a. diese Strings:

* „Development Control nicht verfügbar“
* „Dies ist kein Portfehler...“
* Liste: `API: 127.0.0.1:8000`, `UI/DCC: 127.0.0.1:3001`, `nginx: 127.0.0.1:8080 — nicht SetupHelfer-DCC`
* „Siehe docs/dev-dashboard/PORTS_AND_PROFILES.md“

