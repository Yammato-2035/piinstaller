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

## Data-Runner Pilot (aktuelle Phase)

- Scope: nur `type=data` kann optional ueber isolierten Runner laufen.
- Feature-Schalter: `SETUPHELFER_BACKUP_RUNNER_MODE=thread|systemd-template`
- Default bleibt: `thread`
- Bei `systemd-template` wird fuer `type=data` eine installierte Template-Unit gestartet.
- Fachlicher Status bleibt `status.json` unter `/var/lib/setuphelfer/backup-jobs/<job_id>/status.json`.
- Cancel erfolgt ueber `systemctl stop <unit>`.
- Suspend-Schutz bleibt Pflicht; bei Fehler: `backup.inhibit_failed` + `SYSTEMD-INHIBIT-042`.
- Bekannte Grenze: Full-Backup ist in dieser Phase noch nicht auf Runner migriert.

## Entscheidung: systemd-run nicht als Produktivstart aus dem Backend

- `systemd-run` aus dem gehaerteten Backend ist im Feld nicht zuverlaessig (Policy/Bus/Auth-Abhaengigkeiten).
- Der Fehler zeigte sich bereits als nicht-deterministisches Startproblem (`interactive authentication required`, `failed to connect to bus`).
- Fuer Endkunden ist das kein stabiler Produktivpfad.
- Produktivstart soll ueber installierte, definierte Unit erfolgen:
  - Backend triggert `setuphelfer-backup@<job_id>.service`
  - keine freien transient Units als Standardpfad.

## Template-Unit Entwurf (Produktivziel)

Datei (Installationsziel):

- `/etc/systemd/system/setuphelfer-backup@.service`

Repo-Entwurf:

- `packaging/systemd/setuphelfer-backup@.service`

Grundsaetze:

- Instanzname = `job_id` (`%i`)
- `ExecStart` ruft Runner nur mit `--job-id %i` (plus feste Laufzeitpfade)
- Runner liest Jobkonfiguration aus:
  - `/var/lib/setuphelfer/backup-jobs/%i/job.json`
- keine Parametertunnelung ueber Unit-Namen.

Empfohlene Unit-Eigenschaften:

- `Type=simple`
- `User=root` (begruendet: systemweiter Sleep-Inhibitor + robuste Prozesskontrolle ohne Session-Abhaengigkeit)
- `Group=setuphelfer`
- `SupplementaryGroups=setuphelfer`
- `KillSignal=SIGTERM`
- `TimeoutStopSec=30`
- `NoNewPrivileges=no` nur fuer Runner-Unit (nicht fuer Backend)
- `ProtectSystem=strict`
- `PrivateTmp=yes`
- `ReadWritePaths=/mnt/setuphelfer /var/lib/setuphelfer /var/log/setuphelfer`
- `WorkingDirectory=/opt/setuphelfer/backend`

## Job-Konfigurationsvertrag

Pfad:

- `/var/lib/setuphelfer/backup-jobs/<job_id>/job.json`

Mindestfelder:

- `job_id`
- `backup_type`
- `backup_dir`
- `source`
- `lang`
- `requested_by`
- `created_at`

Regeln:

- Backend schreibt `job.json`.
- Runner liest `job.json`.
- `status.json` bleibt fachliche Statusquelle.
- Keine sensiblen Klartext-Geheimnisse in `job.json`.

## Startmechanismus (Zielbild)

Backend-Trigger:

- `systemctl start setuphelfer-backup@<job_id>.service`

Feature-Schalter bleibt verpflichtend:

- `SETUPHELFER_BACKUP_RUNNER_MODE=thread|systemd-template`
- Default: `thread`

Wenn `systemd-template` aktiv:

- Backend legt `job.json` + initiales `status.json` an.
- Backend startet Template-Unit.
- API gibt `accepted` + `job_id` zurueck.

## Berechtigungen/Polkit (Produktivstrategie)

Beobachtung:

- Start/Stop von Units aus Service-Kontext ist ohne explizite Freigabe nicht robust garantiert.

Option A (empfohlen):

- gezielte Polkit-Regel nur fuer `setuphelfer-backend`:
  - erlaubt `start/stop/status` fuer `setuphelfer-backup@*.service`
  - keine generelle `systemctl`-Freigabe

Option B:

- kleiner root-owned Starter-Helper mit festem Unit-Namensmuster

Bewertung:

- Option A ist transparenter und systemd-nativ.
- Option B ist fallback-tauglich, aber zusaetzliche Binary-/Auditflaeche.

## Testplan (naechste Phase)

1. Template-Unit manuell als root mit Test-`job.json` starten.
2. `status.json` entsteht und wird laufend aktualisiert.
3. Data-Backup laeuft mit `.partial -> .tar.gz` bei Erfolg.
4. `systemd-inhibit` ist im Runner aktiv (kein ungeschuetzter Lauf).
5. Cancel via `systemctl stop setuphelfer-backup@<job_id>.service` funktioniert.
6. API-Startpfad erst nach Polkit/Helper-Freigabe scharf schalten.

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
