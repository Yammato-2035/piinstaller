# Phase 6 – Live-Daten-Anbindung (setuphelfer.de)

Datum: 2026-03-17
Ziel: Echte Systemdaten anzeigen, wenn Backend erreichbar ist, mit robusten Fallback-Zustaenden.

## 1) Gepruefte Backend-Endpunkte

In `backend/app.py` verifiziert:

- `GET /health`
- `GET /api/system-info` (mit `light=true` fuer leichtes Polling)
- weitere verfuegbare Status-Endpunkte:
  - `/api/status`
  - `/api/system/resources`

Fuer die Website wurde bewusst `health + system-info(light)` als robuste Basis gewaehlt.

## 2) Umsetzung in der Website

### 2.1 Neuer Live-Status-Bereich

Datei: `website/setuphelfer-theme/snippets/index.html`

- Neuer Abschnitt `#setuphelfer-live-status` auf der Startseite.
- Anzeigen fuer:
  - Verbindungsstatus
  - CPU-Auslastung
  - RAM frei
  - Speicherbelegung
  - Hostname
  - Uptime
  - letzte Aktualisierung

### 2.2 Polling-/Fetch-Logik

Datei: `website/setuphelfer-theme/assets/js/live-status.js`

- Polling-Intervall: 10 Sekunden
- Healthcheck vor Datenabfrage:
  - prueft `/health`
- Danach Abfrage:
  - `/api/system-info?light=1`
- Endpoint-Fallback-Reihenfolge:
  1. `<origin>/health`
  2. `/health`
  3. `http://localhost:8000/health`

## 3) Fallback-Zustaende (Pflicht)

Implementiert:

- `Ladezustand`
- `Backend verbunden`
- `Setuphelfer laeuft lokal`
- `Backend nicht erreichbar`
- Bei Fehler:
  - Metriken werden auf `-` gesetzt
  - keine Fantasiedaten

## 4) Technische Einbindung

Datei: `website/setuphelfer-theme/functions.php`

- Script registriert:
  - `setuphelfer-live-status` -> `assets/js/live-status.js`

## 5) Erfuellung der Phase

- Keine fragile Einmalabfrage: Ja (intervallbasiertes Polling).
- Healthcheck-basiertes Laden: Ja.
- Echte Daten nur bei API-Antwort: Ja.
- Klare Fehler-/Offline-Zustaende: Ja.
- Keine Fantasiedaten im Offlinefall: Ja.

