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

## Kein Bug

Wenn Port 8080 die Apache/nginx-Default-Seite zeigt, ist das **korrekt** für diesen Port — nicht „DCC kaputt“.
