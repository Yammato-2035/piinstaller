# Backup systemd-run Migration Contract

## Scope

Dieser Vertrag definiert einen kontrollierten Migrationspfad von thread-basierten Backups zu systemd-run Jobs.

Nicht Ziel in dieser Phase:
- produktive Migration
- Entfernen des bestehenden Thread-Modus
- Packaging-/Installer-Änderungen

## 1. Zielarchitektur

Geplanter Laufzeitfluss:

API  
-> `systemd-run` transient unit  
-> `backup_runner.py`  
-> strukturierte JSON-Statusdatei  
-> API liest `status.json` + systemd state

## 2. Statusquelle (fachlich)

Primäre fachliche Statusquelle ist **nicht** ausschließlich Journal.

Pfad:

`/var/lib/setuphelfer/backup-jobs/<job_id>/status.json`

Pflichtfelder:

- `job_id`
- `unit_name`
- `status`
- `code`
- `severity`
- `diagnosis_id`
- `backup_started_at`
- `backup_finished_at`
- `archive_path`
- `abort_reason`
- `progress_optional`

## 3. systemd-Unit-State (technisch)

systemd bleibt technische Laufzeitquelle:

- `ActiveState`
- `SubState`
- `ExecMainStatus`
- `Result`

Fachliche API-Antwort priorisiert `status.json`; systemd ergänzt Laufzeitdiagnose.

## 4. Cancel-Vertrag

Cancel-Operation:

`systemctl stop setuphelfer-backup-<jobid>.service`

Runner-Verhalten bei SIGTERM:

- `status=cancelled`
- `code=backup.cancelled`
- `backup_finished_at` gesetzt
- deterministischer finaler Status in `status.json`

## 5. Fehlervertrag

Bei Fehlern:

- `status=error`
- `code` gesetzt
- `diagnosis_id` gesetzt (falls verfügbar)
- `backup_finished_at` gesetzt
- Teilartefakte als ungültig markieren oder entfernen

## 6. Cleanup-Vertrag

Keine halb-gültigen Archive als Erfolg ausweisen.

Empfohlen:

1. Schreiben nach `<name>.partial`
2. Nach vollständigem Erfolg atomar umbenennen auf finales Archiv

Beispiel:

- `backup.tar.gz.partial`
- bei Erfolg -> `backup.tar.gz`

## 7. Rückfallstrategie

Der bestehende Thread-Modus bleibt aktiv, bis systemd-run Variante vollständig getestet ist.

Rollback muss jederzeit möglich sein:

- Feature-Flag/Startpfad zurück auf Thread-Modus
- keine Entfernung bestehender Endpunkte/Statuscodes in dieser Phase

## Statusentscheidung / Freeze

systemd-run ist aktuell nur Zukunftsoption und bleibt geparkt.

Keine produktive Migration, bevor Backup/Restore vollständig reif und nachgewiesen ist.

Hauptziel bleibt:

- vollständiges Backup
- Verify
- Restore
- bootfähiges Zielsystem

Der Thread-Modus bleibt produktiv, solange folgende Schutzmechanismen wirksam sind:

- `systemd-inhibit` aktiv im produktiven Backup-Lauf
- Paketmanager-Konflikte werden vor Start blockiert
- Paketmanager-Konflikte während Lauf führen zum definierten Abbruch
- Verify läuft erfolgreich auf erzeugten Archiven
- Restore ist bootfähig validiert

## API-Design (Skizze, nicht implementiert)

### `POST /api/backup/create`

- erzeugt `job_id`
- erzeugt Job-Ordner
- startet `systemd-run`
- gibt `job_id` + Unit-Name zurück

### `GET /api/backup/jobs/{job_id}`

- liest `status.json` als fachliche Quelle
- ergänzt systemd state (technisch)

### `POST /api/backup/jobs/{job_id}/cancel`

- ruft `systemctl stop <unit>` auf
- erwartet finalisiertes `status.json` vom Runner

## Risiken vor produktiver Migration

- Inkonsistenz zwischen `status.json` und Unit-State
- unvollständige Finalisierung bei abruptem Systemausfall
- Berechtigungsmodell auf `/var/lib/setuphelfer/backup-jobs`
- sauberer Umgang mit Teilartefakten (`.partial`)

## Entscheidungsregel nächste Phase

Produktive Umstellung erst nach:

- PoC-Start/Stop reproduzierbar
- Cancel sauber (SIGTERM -> finaler Status)
- Statusdatei stabil
- keine Regression in Diagnosecodes/Logging-Vertrag
