# Wissensbasis: DCC Port-Zuordnung

## Merksatz

- **3001** = sehen (UI / Cockpit)
- **8000** = messen (API / Gates / Fleet / Dev-Dashboard)
- **8080** = ignorieren (nginx, nicht SetupHelfer)

## Cockpit-URL

`http://127.0.0.1:3001/?window=cockpit`

## API

Alle Dev-Dashboard- und Fleet-Endpunkte nur unter `http://127.0.0.1:8000/api/...`.

Im Release-Profil: Dev-Routen → `PROFILE_ROUTE_BLOCKED` (erwartbar).

## Frontend-Produktion

Der SPA-Server auf 3001 proxyt **kein** `/api` zum Backend. Das Frontend nutzt direkt `:8000` (`PRODUCTION_WEB_DEFAULT_API`).

## Frontend-Gating (DCC)

- Die Disabled-Page ist an `GET /api/dev-dashboard/status` gebunden (source-of-truth).
- Wenn `/api/dev-dashboard/status` HTTP 200 liefert, muss DCC angezeigt werden — `install_profile`-Snaps von `/api/version` duerfen das nicht blockieren.
- Status-Requests werden mit `cache: no-store` und Query-Param `?t=<Date.now()>` ausgefuehrt, um stale Snapshots zu vermeiden.

## Kein Bug

Wenn Port 8080 die Apache/nginx-Default-Seite zeigt, ist das **korrekt** für diesen Port — nicht „DCC kaputt“.
