# Backup & Restore – Phase 2D Verifikation (Entwicklungsumgebung)

Stand: manuell gepflegt nach lokalen Läufen (kein CI-Automat).

## Umgebung

- Relevant: Linux-Entwicklungsrechner, **nicht** Ziel-Raspberry-Pi.
- Backend: `backend/venv` mit vorhandenen Abhängigkeiten; **keine** neue Paketinstallation im Rahmen von Phase 2D.
- API-Tests: `fastapi.testclient.TestClient` gegen importiertes `app` (kein separater Long-Run-Server nötig).

## Real ausgeführt (Beispielnachweis)

Siehe Projektbericht Phase 2D: exakte Befehle und Ergebnisse der TestClient-Läufe.

Kurz:

- `python3 -m py_compile backend/modules/backup.py backend/app.py`
- `npm run build --prefix frontend`
- HTTP-Tests (TestClient): Verify (fehlend, unzulässiger Pfad, gültiges Mindestarchiv, **ungültiger Dateiinhalt** → `backup.verify_archive_unreadable`), List (ungültig/ok), Delete (fehlend/unzulässig), Restore (dry-run, preview, root gesperrt)
- Async-Backup-Create ohne Sudo: erwartbar `backup.sudo_required` – **Job-Konflikt-Pfad in dieser Session nicht real verifiziert**

## Nicht real belegt hier

- Zielhardware (USB/NVMe), echte Cloud-Provider, Mehrclient-Last, vollständiger Produktiv-Restore.
- Paralleler Long-Job-Konflikt (`backup.job_conflict`), wenn kein erster async-Job ohne Sudo gestartet werden kann.

## Belastbare Aussagen

- Kern-**Fehlerpfade** Verify/List/Delete/Restore (ohne echtes tar-Backup-Erstellen) verhalten sich konsistent zu `code`/`severity`/`status` in den ausgeführten Fällen.
- **Frontend-Build** und **Python-Syntax** der genannten Dateien waren im Prüflauf grün.

## Was nicht behauptet wird

- Produktionsreife, vollständige Abdeckung aller Pfade oder Verhalten auf dem Pi.

---

## Phase 2E – kontrollierte Laufzeit (Erganzung)

**Datum:** manuell dokumentiert nach Phase-2E-Lauf.

### Vorbereitung (sicher, klein)

- Pfade: `/tmp/setuphelfer-test/phase2e/source/` (2 Textdateien + Unterordner), `/tmp/setuphelfer-test/phase2e/backups/` (leeres Ziel).
- Liegen unter der Backend-Allowlist (`/tmp/setuphelfer-test/...`).

### Blocker: kein echter API-Backup-Lauf in dieser Umgebung

- `sudo -n true` schlägt fehl („Passwort ist notwendig“).
- `POST /api/backup/create` (sync und async, `backup_dir` wie oben, `target: local`) **ohne** `sudo_password` liefert konsistent `backup.sudo_required`, `requires_sudo_password: true`.
- **Ohne** vom Nutzer freigegebenes Sudo-Passwort im Request ist hier **kein** tar-Backup über die API ausführbar.

### Zusätzliches fachliches Risiko (auch mit Sudo)

- Die implementierten Typen `full` / `data` / `incremental` führen **kein** reines „Packen nur des Testordners“ aus, sondern archivieren **systemweite Pfade** (z. B. `/` bzw. `/home`, `/var/www`, `/opt`). Das ist für Phase 2E **nicht** als risikoarmer Mini-Test geeignet; ein „harmloser“ Ein-Ordner-Backup-Modus existiert in der API **nicht**.

### Real geprüft (Phase 2E)

- Erneut: `python3 -m py_compile backend/modules/backup.py backend/app.py`, `npm run build --prefix frontend`.
- TestClient: `POST /api/backup/create` sync + async ohne Passwort → `backup.sudo_required`.

### Nicht real geprüft (Phase 2E)

- Echter Job-Lauf, Job-Polling, `backup.job_conflict`, Cancel, List/Verify eines **über die API erzeugten** Backups.

### Freigabe-/Testblocker (ehrlich)

- **Echter Backup-Lauf** und **Job-Pfade** bleiben in dieser Umgebung **ohne interaktives Sudo** und ohne API-„Micro-Backup“-Modus **unbelegt**.
