# Release-Service Script

Automatisiertes Release-Script für PI-Installer, das alle Schritte von der Versionserhöhung bis zum Update der lokalen Installation durchführt.

## Features

- ✅ Automatische Versionserhöhung (Patch oder Feature)
- ✅ Dokumentation und Changelog aktualisieren
- ✅ Tauri-App bauen
- ✅ DEB-Paket erstellen
- ✅ Git Commit und Push nach GitHub
- ✅ Lokale Installation updaten
- ✅ Automatische Fehlerbehebung mit Retry-Logik
- ✅ Detailliertes Logging

## Verwendung

Hilfe und Optionen jederzeit anzeigen:

```bash
bash scripts/release-service.sh --help
```

### Standard (Patch-Version erhöhen)

```bash
bash scripts/release-service.sh
```

Erhöht die Patch-Version (W in X.Y.Z.W) um 1.

### Feature-Version erhöhen

```bash
bash scripts/release-service.sh --feature-bump
```

Erhöht die Feature-Version (Z in X.Y.Z.W) um 1 und setzt W auf 0.

### Ohne lokales Update

```bash
bash scripts/release-service.sh --skip-update
```

Führt alle Schritte aus, außer dem Update der lokalen Installation.

## Ablauf

1. **Version erhöhen**
   - Liest aktuelle Version aus `VERSION`
   - Erhöht Patch- oder Feature-Version
   - Aktualisiert `tauri.conf.json` und `Cargo.toml`

2. **Dokumentation aktualisieren**
   - `debian/changelog`
   - `CHANGELOG.md`
   - `frontend/src/pages/Documentation.tsx`

3. **Tauri-App bauen**
   - Prüft Rust/Cargo
   - Installiert npm-Abhängigkeiten falls nötig
   - Baut Release-Binary

4. **DEB-Paket erstellen**
   - Prüft Build-Abhängigkeiten
   - Bereinigt alte Artefakte
   - Erstellt `.deb`-Paket

5. **Git Commit und Push**
   - Committet alle Änderungen
   - Pusht nach GitHub

6. **Lokale Installation updaten**
   - Installiert das neue DEB-Paket

## Fehlerbehandlung

Das Script behebt automatisch häufige Fehler:

- **Rust/Cargo nicht gefunden**: Hinweis zur Installation
- **npm/node nicht gefunden**: Hinweis zur Installation
- **Git-Konfiguration fehlt**: Automatische Konfiguration
- **DEB-Build-Abhängigkeiten fehlen**: Automatische Installation
- **Build-Cache-Probleme**: Automatische Bereinigung

Bei Fehlern wird das Script bis zu 3 Mal wiederholt, wobei nach jedem Fehler versucht wird, die Ursache zu beheben.

## Log-Datei

Alle Ausgaben werden in `logs/release-service.log` gespeichert. Bei Fehlern können Sie diese Datei prüfen:

```bash
tail -f logs/release-service.log
```

## Voraussetzungen

- Git-Repository mit `origin` remote konfiguriert
- Rust/Cargo installiert (für Tauri-Build)
- Node.js/npm installiert
- `debhelper` und `rsync` installiert (für DEB-Build)
- Sudo-Rechte für Installation und Update (Schritt 6; mit `--skip-update` überspringbar)

## Beispiel-Ausgabe

```
[2026-02-16 14:30:00] Release-Service gestartet
[2026-02-16 14:30:00] Schritt 1: Version erhöhen...
[2026-02-16 14:30:00] Aktuelle Version: 1.3.4.5
[2026-02-16 14:30:00] ✓ Version erhöht: 1.3.4.5 -> 1.3.4.6
[2026-02-16 14:30:01] Schritt 2: Dokumentation aktualisieren...
[2026-02-16 14:30:01] ✓ debian/changelog aktualisiert
[2026-02-16 14:30:02] Schritt 3: Tauri-App bauen...
[2026-02-16 14:35:00] ✓ Tauri-App erfolgreich gebaut
[2026-02-16 14:35:01] Schritt 4: DEB-Paket erstellen...
[2026-02-16 14:36:00] ✓ DEB-Paket erstellt: ../pi-installer_1.3.4.6-1_all.deb
[2026-02-16 14:36:01] Schritt 5: Git Commit und Push...
[2026-02-16 14:36:02] ✓ Git-Commit erstellt
[2026-02-16 14:36:05] ✓ Nach GitHub gepusht
[2026-02-16 14:36:06] Schritt 6: Lokale Installation updaten...
[2026-02-16 14:36:10] ✓ Lokale Installation aktualisiert
[2026-02-16 14:36:10] ✓ Release-Service erfolgreich abgeschlossen!
```

## Troubleshooting

### Script schlägt beim Tauri-Build fehl

- Prüfen Sie ob Rust installiert ist: `cargo --version`
- Prüfen Sie die Log-Datei: `tail -50 logs/release-service.log`
- Bereinigen Sie den Build-Cache: `rm -rf frontend/src-tauri/target`

### Script schlägt beim DEB-Build fehl

- Installieren Sie Build-Abhängigkeiten: `sudo apt install debhelper rsync`
- Prüfen Sie `debian/control` und `debian/changelog`

### Git-Push schlägt fehl

- Prüfen Sie die Remote-Konfiguration: `git remote -v`
- Stellen Sie sicher, dass Sie Push-Rechte haben
- Prüfen Sie ob es Konflikte gibt: `git fetch origin main && git status`

### Lokales Update schlägt fehl (Schritt 6)

- Log prüfen: `tail -50 logs/release-service.log` (apt-Ausgabe wird dort geschrieben)
- Manuell installieren: `sudo apt install -y /tmp/pi-installer-update.deb` (falls die Datei noch existiert)
- Beim nächsten Lauf lokales Update überspringen: `bash scripts/release-service.sh --help` → Option `--skip-update`
