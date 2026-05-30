# Development Control Center — Übersicht (DE)

## Zweck

Das **Development Control Center** ist die zentrale read-only Steuer- und Übersichtszentrale für Setuphelfer-Entwicklung.

## Bereiche (Tabs)

1. **Überblick** — Runtime-Gate, Version, Dev-Server-Modus, Blocker, nächster Prompt
2. **Roadmap** — Meilensteine, Blocker, empfohlener Prompt (Evidence-basiert)
3. **Telemetrie** — Development Server (= Telemetrieserver), `local_lab`-Modus
4. **Rescue/Agent** — Dev Server → Agent → Developer-Profil → ISO pending
5. **Doku & Diagnostik** — Docs/FAQ/KB/Evidence-Zähler, fehlende DE/EN-Paare
6. **Evidence** — Neueste Evidence-Dateien
7. **Betrieb** — Deploy, Backup-Status (read-only)

## Wichtige Regeln

- **Telemetrieserver** = Development Server (`/api/dev-server/*`)
- **`local_lab`** ist der Entwickler-/Labormodus — grün wenn enabled + storage_ok
- **SSH disabled** ist aktuell gewollt — kein Fehler
- **Public uploads disabled** ist aktuell gewollt — kein Fehler
- Roadmap-Ampeln basieren auf **Evidence**, nicht auf UI-Wunsch
- Doku-/FAQ-/KB-Statistiken sind **read-only** (Dateiscan)
- Keine Backup-/Restore-/ISO-/SSH-Aktionen aus der Übersicht

## API

`GET /api/dev-dashboard/control-center-summary`

## Voraussetzung

Lokaler Development Server muss für Telemetrie-Ingest grün sein (`enabled=true`, `storage_ok=true`).
