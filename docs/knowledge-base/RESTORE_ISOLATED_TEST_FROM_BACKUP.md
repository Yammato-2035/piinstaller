# Restore-Test aus (nahezu) realem Backup – isoliert unter `/tmp`

## Zweck

Validierung der **Datei-Restore-Logik** (`restore_files`) in ein **reines Testverzeichnis**, ohne Root-Dateisystem oder produktive Pfade zu beschreiben.

## Relevante Codepfade

- `backend/modules/restore_engine.py` → `restore_files`
- `backend/modules/backup_symlink_safety.py` → `tar_symlink_linkname_allowed` (relative Symlink-Ziele; absolute Ziele werden zugelassen)
- Optional zur Quersicherung: `backend/modules/backup_verify.py` → `verify_deep` (nicht identisch mit Restore, aber gleiche Symlink-Philosophie)

## Ablauf

1. Ziel: `/tmp/setuphelfer-restore-test` – bei Teststart **komplett löschen** und neu anlegen.
2. Archiv:
   - **Variante A:** Umgebungsvariable `SETUPHELFER_RESTORE_TEST_ARCHIVE` oder CLI-Argument = Pfad zu einem **echten** Backup-Archiv (z. B. aus Debian-VM mit `etc/`, `home/`, `opt/`, Manifest mit `type` / `skipped_members`).
   - **Variante B (Standard im Skript):** Es wird ein **synthetischer** `etc/`-Baum unter `/tmp` erzeugt und mit **`create_file_backup`** archiviert – gleicher Engine-Codepfad wie in der Anwendung, aber ohne fremde VM-Dateien.
3. Aufruf `restore_files(..., allowed_target_prefixes=(Path("/tmp/setuphelfer-restore-test"),))` – Allowlist **nicht** lockern.
4. Prüfungen: Verzeichnis `etc/`, Beispieldatei `ImageMagick-7/colors.xml`, Symlinks `alsa/conf.d/50-pipewire.conf` und `alternatives/awk`, JSON-Bericht `/tmp/setuphelfer-restore-test-report.json`.

## Ergebnis (lokal im Entwicklungs-Repo, 2026-04)

- Kommando: `PYTHONPATH=backend python3 tools/setuphelfer_restore_isolated_test.py`
- `restore_files`: **ohne Exception**, `ok=True`
- Symlinks: **als Symlinks** wiederhergestellt (`readlink` stimmt mit synthetischer Quelle überein)
- Pfadknoten: alle Einträge unter `/tmp/setuphelfer-restore-test` (Prüfung **ohne** Auflösung der Symlink-Ziele, sonst würden absolute Ziele fälschlich als „außerhalb“ gewertet)

## Bekannte Grenzen

- **Eigenes VM-Archiv:** Ohne `SETUPHELFER_RESTORE_TEST_ARCHIVE` werden keine produktionsexakten Pfade wie auf einer spezifischen VM geprüft – dafür Variable setzen und Skript erneut laufen lassen.
- **Absolute Symlink-Ziele:** technisch und sicherheitspolitisch bewusst erlaubt; beim späteren **Folgen** des Links verlässt man den Restore-Baum – kein Widerspruch zu einem isolierten Datei-Restore-Test.
- **Full-Recovery:** weiterhin nicht bewiesen (kein Reboot, kein Root-Restore).

## Fazit-Formulierung

Für den geprüften Lauf: **Restore auf Dateisystemebene plausibel** (Struktur + Symlink-Metadaten + Allowlist + kein Schreiben nach `/`).
