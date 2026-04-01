# Backup/Restore Real-Test – Struktur (Vorbereitung)

## Ziel
Reale, reproduzierbare Tests für Backup/Restore vorbereiten – ohne sie automatisch auszuführen.

---

## Testdaten (geplant)

- **Gültiges Backup**:
  - Beispielpfad: `/mnt/backups/pi-backup-full-valid.tar.gz`
  - Inhalt: kleine, aber repräsentative Verzeichnisstruktur (Dokumente, Konfigurationsdateien, Dummy-Daten)

- **Beschädigtes Backup**:
  - Beispielpfad: `/mnt/backups/pi-backup-broken.tar.gz`
  - Inhalt: absichtlich abgeschnittenes oder manipuliertes Archiv

- **Ungültiger Pfad**:
  - Beispiel: `/etc/shadow` oder `/root/does-not-exist.tar.gz`

Diese Pfade dienen als Platzhalter und müssen auf dem Zielsystem manuell erzeugt/angepasst werden.

---

## Geplanter Testablauf (ohne automatische Ausführung)

### 1. Verify-Tests

1. **Gültiges Backup**
   - Eingabe:
     - `backup_file`: gültiges Archiv
     - `mode`: `basic` und `deep` (falls unverschlüsselt bzw. Schlüssel vorhanden)
   - Erwartung:
     - `api_status`: `ok`
     - `results.valid`: `true`
     - sinnvolle `file_count` und Beispiel-Dateien

2. **Ungültiger Pfad**
   - Eingabe:
     - `backup_file`: Pfad außerhalb der erlaubten Wurzeln oder nicht existent
   - Erwartung:
     - `api_status`: `error`
     - verständliche Fehlermeldung (`Pfad ungültig` / `Datei existiert nicht`)

3. **Beschädigtes Backup**
   - Eingabe:
     - `backup_file`: beschädigtes Archiv
   - Erwartung:
     - `api_status`: `error`
     - `results.valid`: `false`
     - Fehlertext mit Hinweis auf beschädigtes Archiv

### 2. Restore-Tests

1. **Dry-Run**
   - Eingabe:
     - `mode`: `dry-run`
     - `backup_file`: gültiges Archiv
   - Erwartung:
     - keine Schreiboperationen
     - Rückgabe von:
       - `analysis`
       - `total_entries`
       - `backup_file`

2. **Preview (Sandbox-Restore)**
   - Eingabe:
     - `mode`: `preview`
     - `backup_file`: gültiges Archiv
     - `sudo_password`: manuell bereitgestellt
   - Erwartung:
     - Entpacken nach: `/mnt/setuphelfer-restore-preview/<timestamp>`
     - `api_status`: `ok` bei Erfolg
     - Rückgabe von:
       - `preview_dir`
       - `analysis`
       - `total_entries`

3. **Blockierte Archive**
   - Eingabe:
     - `backup_file`: Archiv mit Pfad-Traversal, Symlinks oder Sonderdateien
   - Erwartung:
     - `api_status`: `error`
     - `analysis.blocked_entries` nicht leer

---

## Dokumentation der realen Testläufe (auszufüllen bei Ausführung)

> Dieser Abschnitt ist eine Vorlage und muss nach realen Tests ausgefüllt werden.

Für jeden Real-Test:

- **Eingabedatei**: `...`
- **Modus**: `verify basic|deep`, `restore dry-run|preview`
- **Zielpfad / Preview-Verzeichnis**: `...`
- **Ausgeführter Befehl / API-Call**: `...`
- **Ergebnis**:
  - `status` / `api_status`
  - `message`
  - relevante Felder aus `data`
- **Fehlerfälle**:
  - `...`
- **Nicht getestete Aspekte / offene Punkte**:
  - `...`

---

## Offene Punkte (Stand Vorbereitung)

- Real vorhandene Test-Backups müssen auf dem Zielsystem erzeugt oder bereitgestellt werden.
- Eine automatische Testausführung (pytest oder ähnliche Frameworks) ist bewusst **nicht** Teil dieser Phase.
- Status-Flags in den Backup-Einstellungen (`backup.state`) können genutzt werden, um erfolgreiche Real-Tests zu markieren (`restore_preview_ok`, `restore_real_tested`).

