# Security Review: AppStore

## Kurzbeschreibung

App-Katalog mit Installation. API: /api/apps, /api/apps/{id}/status, /api/apps/{id}/install. Installiert nur Apps aus festem Katalog (Docker/apt).

## Angriffsfläche

Eingaben: app_id (aus Katalog). Kritische Aktionen: Docker/apt je nach App.

## Schwachstellen

app_id muss strikt aus Katalog-Whitelist sein; keine beliebigen IDs an Install übergeben.

## Empfohlene Maßnahmen

Whitelist prüfen vor Install; bereits APPS_CATALOG im Backend.

## Ampelstatus

**GRÜN.**

## Betroffene Dateien

backend/app.py: /api/apps/*, APPS_CATALOG. frontend/src/pages/AppStore.tsx.
