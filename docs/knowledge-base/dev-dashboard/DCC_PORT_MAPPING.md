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
- Fix committed in `4fb72ee`; Produktions-Bundle unter `/opt` muss per `deploy-to-opt.sh` aktualisiert werden, bevor Browser-Smoke gilt.
- Blank-Screen-Fail-safe: Marker `DCC_BOOT_DIAGNOSTICS_V1` im Bundle; Diagnosepanel `dcc-boot-diagnostics` immer sichtbar.
- Live-Ingest 2026-06-05: `/opt` + served `index-FgGYQFBB.js` enthalten alle Marker; local_lab + release restore belegt; `blank_dcc_screen` resolved; DCC **grün**.

## Kein Bug

Wenn Port 8080 die Apache/nginx-Default-Seite zeigt, ist das **korrekt** für diesen Port — nicht „DCC kaputt“.
