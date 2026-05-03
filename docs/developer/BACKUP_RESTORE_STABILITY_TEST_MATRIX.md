# Backup/Restore Stability Test Matrix

## Scope

Diese Matrix validiert den aktuellen produktiven Thread-Backup-Pfad.
`systemd-run` ist nicht produktiv aktiviert und nicht Teil dieser Testausfuehrung.

## Harte GO/NO-GO Gates

## Partial-Archive-Schutzvertrag

- Backup schreibt waehrend Lauf ausschliesslich auf `<name>.tar.gz.partial`.
- Finale `<name>.tar.gz` wird erst nach erfolgreichem Backup inklusive Manifest atomar erzeugt.
- Bei Fehler/Cancel/Timeout/Paketkonflikt darf keine gueltig wirkende finale `.tar.gz` aus dem aktuellen Lauf verbleiben.
- Verify muss `.partial` strikt blockieren.

### GO nur wenn alle Punkte erfuellt sind

- Full-Backup erfolgreich
- Verify basic erfolgreich
- Verify deep erfolgreich
- Restore erfolgreich
- Zielsystem bootet
- Backend laeuft
- UI erreichbar
- keine Paketmanager-Kollision waehrend Backup
- kein Suspend-Abbruch
- keine halb gueltigen Archive als Erfolg

### NO-GO wenn einer der Punkte eintritt

- Backup bricht ohne klaren Code ab
- Verify schlaegt fehl
- Restore bootet nicht
- Archiv wird nach Fehler als gueltig behandelt
- API meldet Erfolg trotz Fehler

## Testfaelle

### TEST 1: Datenbackup auf externer NVMe

- Ziel: Produktiver Datenbackup-Pfad funktioniert auf externem Ziel.
- Startbedingung: Externe NVMe unter erlaubt-mount (`/mnt/setuphelfer/backups`) verfuegbar, Target-Check OK.
- Durchfuehrung: `POST /api/backup/create` mit `type=data`, `backup_dir=/mnt/setuphelfer/backups`.
- Erwartetes Ergebnis: `status=success`, `code=backup.success`, Archiv vorhanden, `backup_finished_at` gesetzt.
- Abbruchkriterium: API-Fehlercode, fehlendes Archiv, Permission-/Target-Fehler.
- Belegpflicht: API-Response, Dateiliste Zielpfad, strukturierter Jobstatus.

### TEST 2: Full-Backup auf externer NVMe

- Ziel: Full-Backup laeuft stabil im aktuellen Thread-Modus.
- Startbedingung: Genuegend Speicher, Target-Check OK, keine laufende Paketaktivitaet.
- Durchfuehrung: `POST /api/backup/create` mit `type=full`.
- Erwartetes Ergebnis: `status=success`, Manifest eingebettet, `backup_finished_at` gesetzt.
- Abbruchkriterium: Timeout, tar-Fehler, ungeklaerter Abbruch.
- Belegpflicht: API-Response, Logs, Archiv vorhanden, Manifest-Nachweis.

### TEST 3: Lockscreen waehrend Backup

- Ziel: Backup wird durch Lockscreen nicht unterbrochen.
- Startbedingung: Laufendes Full- oder Datenbackup.
- Durchfuehrung: Session sperren (`loginctl lock-session`), Backup weiter beobachten.
- Erwartetes Ergebnis: Job laeuft weiter und endet definiert (success oder klarer Fehlercode).
- Abbruchkriterium: Harter Stillstand ohne Fortschritt und ohne Code.
- Belegpflicht: Zeitstempel Jobstatus, Logs vor/nach Lock, finale API-Antwort.

### TEST 4: Paketmanager-Aktivitaet vor Backup

- Ziel: Preflight-Gate blockiert Backupstart bei apt/dpkg-Aktivitaet.
- Startbedingung: Simulierte/echte Paketmanager-Aktivitaet laeuft.
- Durchfuehrung: Backupstart ueber API waehrend apt/dpkg aktiv ist.
- Erwartetes Ergebnis: `status=error`, `code=backup.blocked_package_activity`, Diagnose (`UPDATE-CONFLICT-041`).
- Abbruchkriterium: Backup startet trotz aktiver Paketoperation.
- Belegpflicht: API-Response inkl. `active_package_processes`, Prozessbeleg.

### TEST 5: Paketmanager-Aktivitaet waehrend Backup

- Ziel: Runtime-Konflikt fuehrt zu kontrolliertem Abbruch.
- Startbedingung: Laufendes Backup ohne initiale Paketaktivitaet.
- Durchfuehrung: Waehren des Backups apt/dpkg starten.
- Erwartetes Ergebnis: Backup endet mit `status=error`, `code=backup.blocked_package_activity`, `backup_finished_at` gesetzt.
- Abbruchkriterium: Backup laeuft trotz Konflikt ungeprueft durch.
- Belegpflicht: API-Response, Prozessbeleg, Logs mit Abbruchgrund.

### TEST 6: Verify basic direkt nach Backup

- Ziel: Frische Archive bestehen Basic-Verify.
- Startbedingung: Erfolgreiches Backup-Archiv vorhanden.
- Durchfuehrung: `POST /api/backup/verify` auf gerade erzeugtes Archiv (basic/shallow).
- Erwartetes Ergebnis: Verify-Erfolgscode, keine Regression.
- Abbruchkriterium: Verify-Fehler auf formal gueltigem Archiv.
- Belegpflicht: Verify-Response, Datei-/Archivlesbarkeit.

### TEST 6a: Verify auf `.partial` (Blockade)

- Ziel: Sicherstellen, dass unvollstaendige Archive nicht als gueltig verifiziert werden.
- Startbedingung: Vorhandene Testdatei mit Suffix `.partial`.
- Durchfuehrung: `POST /api/backup/verify` auf `<backup>.tar.gz.partial`.
- Erwartetes Ergebnis: `status=error`, `code=backup.verify_partial_not_allowed`.
- Abbruchkriterium: Verify akzeptiert `.partial` oder liefert unklaren Erfolg.
- Belegpflicht: API-Response mit Fehlercode und Diagnose.

### TEST 6b: Inhibit-Fehler im Service-Kontext

- Ziel: Backup darf ohne aktiven Suspend-Schutz nicht anlaufen.
- Startbedingung: `systemd-inhibit` scheitert im Service-Kontext (z. B. Access denied / Binary nicht nutzbar).
- Durchfuehrung: `POST /api/backup/create` (data/full) im betroffenen Service-Kontext.
- Erwartetes Ergebnis: `status=error`, `code=backup.inhibit_failed`, `diagnosis_id=SYSTEMD-INHIBIT-042`.
- Regel: Kein ungeschuetzter tar-Lauf ohne Suspend-Schutz.
- Abbruchkriterium: generisches `backup.failed`, oder Backup laeuft ohne Inhibit weiter.
- Belegpflicht: API-Response inkl. `inhibit_available`, `inhibit_error`, `suspend_guard_active=false`, `partial_deleted`.

### TEST 7: Verify deep direkt nach Backup

- Ziel: Integritaet und Inhaltspruefung direkt nach Backup.
- Startbedingung: Erfolgreiches Backup und verfuegbare Deep-Verify-Pfade.
- Durchfuehrung: Deep-Verify ueber API auf gleiches Archiv.
- Erwartetes Ergebnis: `backup.verify_success` (oder definierter Integritaets-Fehlercode).
- Abbruchkriterium: Uneindeutiger Verify-Status ohne Diagnosecode.
- Belegpflicht: Verify-Response, Details/Diagnose-ID, Laufzeitmarker.

### TEST 7a: Runner Data-Backup (systemd-Pilot)

- Ziel: Data-Backup kann optional isoliert ueber Runner laufen.
- Startbedingung: `SETUPHELFER_BACKUP_RUNNER_MODE=systemd`.
- Durchfuehrung: `POST /api/backup/create` mit `type=data`.
- Erwartetes Ergebnis: transient Unit gestartet, `status.json` vorhanden, `.partial` waehrend Lauf, final `.tar.gz` nur bei Erfolg.
- Abbruchkriterium: kein Runner-Start, kein Statusvertrag, oder `.partial` bleibt als scheinbar gueltiges Archiv.
- Belegpflicht: API-Response, Unit-Name, `status.json`, Dateiliste.

### TEST 7b: Runner Cancel

- Ziel: Cancel stoppt die Runner-Unit deterministisch.
- Startbedingung: laufender Runner-Data-Job.
- Durchfuehrung: `POST /api/backup/jobs/{job_id}/cancel`.
- Erwartetes Ergebnis: `systemctl stop <unit>`, final `status=cancelled`, `code=backup.cancelled`, kein finales Archiv aus Abbruchlauf, keine `.partial`-Reste.
- Abbruchkriterium: Cancel ohne finalen Status oder mit verbleibendem Teilartefakt.
- Belegpflicht: Cancel-Response, finales `status.json`, Dateiliste.

### TEST 7c: Runner Paketmanager-Konflikt

- Ziel: laufende Paketaktivitaet blockiert Runner sicher.
- Startbedingung: laufender Runner-Data-Job.
- Durchfuehrung: waehrend Lauf apt/dpkg Aktivitaet starten.
- Erwartetes Ergebnis: `status=error`, `code=backup.blocked_package_activity`, `diagnosis_id=UPDATE-CONFLICT-041`, `.partial` Cleanup.
- Abbruchkriterium: Backup laeuft trotz Konflikt ungeprueft weiter.
- Belegpflicht: API/Statusdatei, Prozessbeleg, Dateiliste.

### TEST 8: Restore Preview

- Ziel: Restore-Preview erkennt Risiken vor produktivem Restore.
- Startbedingung: Archiv vorhanden, Zielpfad validierbar.
- Durchfuehrung: Restore-Preview-Endpunkt ausfuehren.
- Erwartetes Ergebnis: Strukturierte Preview mit klarer Entscheidung (freigegeben/blockiert).
- Abbruchkriterium: Preview ohne verwertbare Risikoaussage.
- Belegpflicht: API-Response inkl. Diagnosecodes und Risikoindikatoren.

### TEST 9: Restore auf Zielsystem/VM

- Ziel: Restore-Prozess laeuft technisch sauber durch.
- Startbedingung: Erfolgreiche Preview, Testzielsystem oder VM bereit.
- Durchfuehrung: Restore nach Freigabe auf Testziel ausfuehren.
- Erwartetes Ergebnis: Restore-Endpunkt erfolgreich, keine stillen Fehler.
- Abbruchkriterium: Restore ohne klaren Fehlercode fehlgeschlagen.
- Belegpflicht: API-Response, Zielsystem-Logs, Artefaktpruefung.

### TEST 10: Boot-Test nach Restore

- Ziel: Wiederhergestelltes Zielsystem bootet.
- Startbedingung: Abgeschlossener Restore auf Testziel.
- Durchfuehrung: Neustart des Zielsystems.
- Erwartetes Ergebnis: System erreicht nutzbaren Boot-Zustand.
- Abbruchkriterium: Bootloop, Notfallmodus, Login dauerhaft blockiert.
- Belegpflicht: Bootstatus (`systemctl is-system-running`), relevante Boot-Logs.

### TEST 11: Setuphelfer Backend nach Restore erreichbar

- Ziel: Backend-Dienst ist nach Restore funktionsfaehig.
- Startbedingung: Zielsystem erfolgreich gebootet.
- Durchfuehrung: Backend-Service pruefen und Health/API-Endpunkt aufrufen.
- Erwartetes Ergebnis: Service aktiv, API antwortet konsistent.
- Abbruchkriterium: Backend startet nicht oder antwortet fehlerhaft.
- Belegpflicht: Service-Status, API-Response, Fehlercodes falls vorhanden.

### TEST 12: Setuphelfer UI nach Restore erreichbar

- Ziel: UI ist nach Restore nutzbar.
- Startbedingung: Backend aktiv, Frontend deployt.
- Durchfuehrung: UI im Browser oeffnen und Kernfluss laden.
- Erwartetes Ergebnis: UI erreichbar, keine kritischen Ladefehler.
- Abbruchkriterium: UI nicht erreichbar oder blockierende Fehler.
- Belegpflicht: Erreichbarkeitstest, UI-Fehlerprotokoll/Screenshot.

## Auswertungsregel

Freigabe fuer naechste Stufe nur bei 12/12 bestandenen Pflichttests oder dokumentierter, fachlich akzeptierter Restabweichung mit klarer Risikoentscheidung.
