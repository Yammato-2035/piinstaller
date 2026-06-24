# MSI UI Safe-Walk Checkliste (2026-06-24)

**Payload-Zielversion:** 1.9.16.3 (nach Stick-Update)  
**Modus:** Non-destructive — kein Backup, Restore, Partitionieren, Shutdown final

## Voraussetzungen

- Dev-Rettungsstick mit Payload ≥ 1.9.16.3
- SETUP_LOGS-Partition beschreibbar
- Screenshot-Tool auf Stick (grim/scrot/import/maim — mindestens eines)

## Operator-Schritte

### 1. Boot

- [ ] MSI vom Rettungsstick booten
- [ ] Boot-Splash/Fortschritt sichtbar
- [ ] Startmenü erscheint

### 2. Screenshot Startmenü

```bash
./scripts/rescue-live/capture-rescue-screenshot.sh start-menu
```

- [ ] PNG unter `SETUP_LOGS/screenshots/`
- [ ] JSON-Metadaten daneben

### 3. Startmenü visuell prüfen

- [ ] Logo **groß** (nicht Mini-Logo in Toolbar)
- [ ] Sprache DE/EN in Toolbar sichtbar
- [ ] Shutdown-Button sichtbar
- [ ] Tiles als Karten, **nicht** volle Bildschirmbreite
- [ ] Tiles reagieren auf Klick

### 4. Safe-Walk aktivieren

URL: `http://127.0.0.1:8000/rescue.html?safe_walk=1`  
oder `export RESCUE_UI_SAFE_WALK=1` vor Kiosk-Start

- [ ] Banner „Safe-Walk aktiv“ sichtbar

### 5. Alle Bereiche öffnen (nur Navigation)

| Bereich | Geöffnet | Screenshot-Label |
|---------|----------|------------------|
| Analyse | [ ] | `analyze` |
| Backup | [ ] | `backup-panel` |
| Restore/Preview | [ ] | `restore-preview` |
| Partitionen | [ ] | `partitions` |
| Netzwerk | [ ] | `network` |
| Einstellungen | [ ] | `settings` |
| Logs/System | [ ] | `system-logs` |

```bash
./scripts/rescue-live/capture-rescue-screenshot.sh <label>
```

### 6. SETUP_LOGS prüfen

- [ ] Verzeichnis `screenshots/` enthält alle PNG + JSON
- [ ] SHA256 in JSON stimmt mit Datei überein

### 7. Entscheidung

| Ergebnis | Aktion |
|----------|--------|
| UI vollständig bedienbar | **GELB→GRÜN** — Backup-Discovery als Nächstes (ohne Backup-Start) |
| UI blockiert | **ROT** — kein Backup-Test, Issue dokumentieren |

## Abbruchkriterien (sofort ROT)

- Tiles nicht klickbar
- Sprache oder Shutdown unsichtbar
- Kein Screenshot speicherbar auf SETUP_LOGS
- Safe-Walk führt zu Shutdown/Reboot/Backup-Execute

## Evidence ablegen

`docs/evidence/msi/MSI_UI_SAFE_WALK_<datum>.md` mit Screenshot-Pfaden und Status pro Bereich.
