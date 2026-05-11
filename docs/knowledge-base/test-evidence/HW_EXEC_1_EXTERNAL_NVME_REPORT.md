# HW-EXEC-1 Report (Externe NVMe)

Scope: nur `HW1-01` bis `HW1-05` auf externer NVMe.  
Wichtig: reale Ausfuehrung, keine Erfolgssimulation.

## Ergebnisuebersicht

- HW1-01: **success** -> `EVID-2026-HW1-R11` (Repeat nach FIX-2..FIX-8; frueher `EVID-2026-HW1-01`)
- HW1-02: **success** -> `EVID-2026-HW1-R12` (Repeat; frueher `EVID-2026-HW1-02`)
- HW1-03: **success** -> `EVID-2026-HW1-03` (kontrollierte Negativtests, 2026-04-27)
- HW1-04: **success** -> `EVID-2026-HW1-04` (2026-04-27, Restore-Preview + Zielvalidierung)
- HW1-05: **success** -> `EVID-2026-HW1-05` (2026-04-27, Preview-Analyse + erweiterte Zielvalidierung)

## Pro-Test Bewertung (Pflichtfragen)

### HW1-01
- Diagnose plausibel: ja (`PERM-GROUP-008`, `OWNER-MODE-023`) fuer die **Erstausfuehrung** oben.
- Ursache korrekt: ja, Zielpfad nicht beschreibbar fuer Backend-User.
- Neue Diagnose noetig: nein.
- FAQ erweitern: nein.
- **Nach R11 (2026-04-27):** E2E-Repeat auf externer ext4-NVMe mit `type=data` und `SETUPHELFER_DATA_BACKUP_SOURCES` erfolgreich; Evidence `EVID-2026-HW1-R11`, Matrix `HW1-01` = `success`.

### HW1-02
- Diagnose plausibel: ja (gleiches Rechteproblem wie HW1-01) fuer die **Erstausfuehrung** oben.
- Ursache korrekt: ja, Verschluesselungspfad wurde gar nicht erreicht.
- Neue Diagnose noetig: nein.
- FAQ erweitern: nein.
- **Nach R12 (2026-04-27):** Verschluesseltes Daten-Backup (GPG) inkl. Verify deep und Preview mit Testpasswort erfolgreich; Negativtests mit falschem Passwort liefern deterministische Fehlercodes. Evidence `EVID-2026-HW1-R12`.

### HW1-03
- Diagnose plausibel: ja (`permission denied` beim List/Verify-Vorlauf).
- Ursache korrekt: ja, Lesezugriff auf Backup-Mount blockiert.
- Neue Diagnose noetig: nein.
- FAQ erweitern: nein.

### HW1-04
- **Stand 2026-04-27 (HW-EXEC-1-04):** **success** — Baseline-Backup (`type=data`, `target=local`) auf `/mnt/setuphelfer/backups/test-run`, Verify `mode=deep` (`backup.verify_success`), Restore Preview (`backup.restore_preview_ok`, `blocked_entries=[]`). Preview-Verzeichnis liegt unter **systemd `PrivateTmp`** des Backends; Inhaltsabgleich **MANIFEST.json**, **README.txt**, **sample.json** daher zusätzlich per `tar -xOzf` aus dem Archiv und mit Verify-`sample_files` abgesichert.
- **Zielvalidierung:** (A) Backup-Ziel unter `/media/...` → `backup.path_invalid` / **STORAGE-PROTECTION-005**. (B) absichtlich nicht beschreibbares Unterverzeichnis unter `/mnt/setuphelfer/backups/test-run` → `backup.backup_target_not_writable` / **PERM-GROUP-008**. (C) künstliches Traversal-Archiv → `backup.restore_blocked_entries` / **RESTORE-PATH-004**. Keine HTTP-500, keine stillen Erfolge auf den Negativpfaden.
- **Hinweis:** `GET /api/backup/list` kann je nach `/mnt`-Mount-Auflösung weiterhin **STORAGE-PROTECTION-004** melden; End-to-End für HW1-04 nutzte direktes `POST /api/backup/create` mit explizitem `backup_dir` (wie in HW1-01 R11).
- Neue Diagnose noetig: nein (bestehende IDs).
- FAQ: optionaler Kurzabschnitt zu PrivateTmp vs. Operator-`ls` auf `preview_dir` — nicht zwingend, wenn Report/Evidence ausreichen.

### HW1-05
- Diagnose plausibel: ja (`STORAGE-PROTECTION-005`, `PERM-GROUP-008`, `RESTORE-PATH-004`) für die gezielten Blockadefälle.
- Ursache korrekt: ja, erwartete Sicherheitsgrenzen wurden deterministisch ausgelöst.
- Neue Diagnose noetig: nein.
- FAQ erweitern: optionaler Hinweis zu `PrivateTmp`/`preview_dir` Sichtbarkeit.

## Abbruch-/Sicherheitsregel

Bei kritischen Fehlern wurde kein undokumentiertes Weiterprobieren durchgefuehrt.
Jeder Test hat genau einen eigenen EvidenceRecord erhalten.

## Nachbereitung FIX-1 (ohne erneute Realhardware)

Ziel: HW1-01 bis HW1-05 **erneut ausfuehrbar** machen unter produktionsnahen Bedingungen (kein `/media/<user>`, kein `sudo` im Tar-/Verify-/Preview-Pfad, `NoNewPrivileges=true` im Backend).

Umgesetzt im Repo:

- `scripts/install-system.sh` und `debian/postinst`: legen `/mnt/setuphelfer` und `/mnt/setuphelfer/backups` an mit **root:setuphelfer** und **0770** (Gruppe `setuphelfer` muss existieren; Dienstnutzer ist Mitglied).
- `setuphelfer-backend.service` / `debian/setuphelfer-backend.service`: **NoNewPrivileges=true**, **ReadWritePaths** inkl. `/mnt/setuphelfer`, **RestrictSUIDSGID=yes** (Tar ohne setuid-sudo).
- `app.py` (`_do_backup_logic`): **tar** laeuft als Backend-Prozess **ohne sudo**; Cleanup/Chmod nur mit sudo, wenn explizit Passwort im Store und Owner-Abweichung.

**Erneuter Realtest:** nicht im Repo ausgefuehrt. Nach Installation/Upgrade: NVMe unter z. B. `/mnt/setuphelfer/backups` mounten (siehe `HW_TEST_1_EXECUTION_GUIDE.md`), Backend neu starten, dann HW1-01..05 erneut fahren.

**Verbleibendes Risiko:** Volles Root-Filesystem-Backup (`tar` von `/`) kann einzelne root-only-Pfade ueberspringen oder melden — fuer HW1-01..05 zaelt Schreiben des Archivs auf das **gruppenfaehige** Ziel, nicht Vollstaendigkeit jeder Root-Datei.

---

## HW-EXEC-1-REPEAT (Phase, Stand Dokumentation)

**Ziel:** HW1-01..05 nach FIX-1 erneut auf **externer NVMe** unter `/mnt/setuphelfer/backups/...` mit vollstaendiger Evidence.

**Ausgefuehrt in dieser Repo-/CI-Umgebung:** **nein** — keine externe NVMe, kein `setuphelfer-backend`, keine API/UI gegen Zielsystem. Daher **keine** neuen belastbaren Outcomes (`success`/`failed` Kette) und **keine** fingierten Evidence-Dateien im Commit (`data/` ist zusaetzlich gitignoriert).

**Repo-Artefakte fuer den Zielhost:**

| Artefakt | Zweck |
|----------|--------|
| `docs/knowledge-base/test-evidence/HW_EXEC_1_REPEAT_INSTRUCTIONS.md` | Schrittfolge, Evidence-Pflicht, SUCCESS-Definition, Matrix-Update |
| `data/diagnostics/hw_test_1_matrix.json` | Pro HW1-01..05 Feld `hw_exec_1_repeat_post_fix1` mit `status: not_run` bis zur Host-Ausfuehrung |
| `scripts/diagnostics/new_evidence_record.py` | Stubs fuer `EVID-2026-HW1-R..` anlegen |

**Nach Host-Lauf (Operator):** `hw_exec_1_repeat_post_fix1` auf `passed`/`failed`/`inconclusive`/`blocked` setzen, `evidence_id` eintragen, diesen Abschnitt und die Ergebnisuebersicht oben ersetzen oder ergaenzen.

**Diagnose/FAQ (Nachpruefung ohne neue Laeufe):** keine zusaetzliche Katalog-ID noetig; bei erneutem NNP-Verstoss weiter `SYSTEMD-NNP-031`; Mount/Rechte weiter STORAGE-/PERM-FAQs.

**Service-Konflikt-Schutz (Repo, kein neuer HW1-Claim):** Konflikterkennung in `backend/core/service_conflict_guard.py`, lesend `GET /api/system/service-conflicts`, Preflight in `scripts/start-backend.sh`; Diagnosefaelle `SERVICE-CONFLICT-033` bis `036` (siehe `docs/knowledge-base/diagnostics/SERVICE_CONFLICTS.md`). Ziel: ein klarer Owner auf **:8000** vor belastbaren HW1-01-Folgelaeufen (z. B. R09); kein behaupteter HW1-Erfolg durch diese Aenderung allein.

### RUNTIME-SYNC (Readiness Gate 1), 2026-04-27

- **Ausgangslage:** `GET /api/system/service-conflicts` lieferte zunaechst `404 Not Found`, obwohl `/api/version` bereits `1.5.0.0` war.
- **Ursache:** Laufzeit unter `/opt/setuphelfer` war nicht auf dem aktuellen Repo-Stand (Route noch nicht enthalten), Prozess lief aber korrekt auf `setuphelfer-backend.service`.
- **Massnahme:** Runtime-Sync Repo -> `/opt/setuphelfer` (ohne `.git`, ohne `data/diagnostics/evidence/*`), danach `systemctl daemon-reload` und `systemctl restart setuphelfer-backend`.
- **Validierung:** Endpoint antwortet nun mit JSON (`conflicts`, `active_services`, `port_owner`, `runtime_version`), `/api/version` bleibt `1.5.0.0`, Listener auf `:8000` bleibt `setuphelfer-backend` (`/opt/setuphelfer/backend/venv/bin/python3 -m uvicorn ...`).
- **Bewertung:** **Gate 1 ist gruen**. Kein HW1-Produktivtest in diesem Schritt; nur Deploy-/Runtime-Sync.

### HW1-01 Repeat-Lauf (EVID-2026-HW1-R09), 2026-04-27

- **outcome:** `failed` (kein E2E-Lauf, Abbruch nach Backup-Fehler ohne Workaround).
- **Pre-Check:** voll gruen (`/api/system/service-conflicts` ohne Konflikte, `should_block_start=false`, `/api/version=1.5.0.0`, `findmnt` mit ext4 auf `/dev/sda4`, Rechte auf `test-run`/`test-data` = `root:setuphelfer drwxrws---`, `SETUPHELFER_DATA_BACKUP_SOURCES=/mnt/setuphelfer/test-data`).
- **Backup:** `POST /api/backup/create` (`type=data`, `target=local`) antwortete direkt mit `status=error`, `code=backup.path_invalid`, `details.reason=STORAGE-PROTECTION-004: Mount-Quelle ist kein einfaches Blockgerät (z. B. mapper)`.
- **Verify/Preview:** **nicht gestartet** (Vorgabe: bei erstem Fehler abbrechen, kein Workaround).
- **Diagnoseeinschaetzung:** `STORAGE-PROTECTION-004` (confirmed).
- **Bewertung:** HW1-01 in R09 **nicht bestanden**; naechster Lauf erst nach Klaerung/Fix der Storage-Protection-Blockade.

### FIX-7 Vorbereitung (ohne neuen HW-Lauf), 2026-04-27

- **Ursache aus R09 praezisiert:** `findmnt` liefert fuer denselben Target-Pfad sowohl `systemd-1 autofs` als auch das reale ext4-Device (`/dev/sda4`); die bisherige Source-Ermittlung nahm den autofs-Layer als alleinige Quelle.
- **Code-Fix:** `safe_device.validate_write_target()` nutzt nun eine robuste Mount-Aufloesung (`findmnt -J -T`, optional rekursiv), erkennt den autofs/systemd-automount-Layer und ermittelt konservativ das reale Blockgeraet; `/dev/disk/by-uuid/*` wird auf echtes Blockdevice aufgeloest.
- **Sicherheitsrahmen unveraendert:** keine allgemeine Freigabe fuer `mapper`/LVM, kein `/media`-Write, bei Unsicherheit weiterhin `STORAGE-PROTECTION-004`.
- **Status:** Kein HW-Erfolg behauptet; R10 ist erst nach erneutem Real-Run mit Backup->Verify->Preview belastbar bewertbar.

### HW1-01 Repeat-Lauf (EVID-2026-HW1-R10), 2026-04-27

- **outcome:** `failed` (Abbruch nach Backup-Fehler, kein Workaround).
- **Pre-Check:** voll gruen (`/api/system/service-conflicts` konfliktfrei, `should_block_start=false`, `/api/version=1.5.0.0`, Zielrechte korrekt, Datenquelle gesetzt, Schreibprobe erfolgreich).
- **Backup:** `POST /api/backup/create` (`type=data`, `target=local`) antwortete erneut sofort mit `status=error`, `code=backup.path_invalid`, `details.reason=STORAGE-PROTECTION-004: Mount-Quelle ist kein einfaches Blockgerät (z. B. mapper)`.
- **Verify/Preview:** gemaess Run-Regel **nicht gestartet**.
- **Diagnoseeinschaetzung:** `STORAGE-PROTECTION-004` (confirmed).
- **Bewertung:** HW1-01 in R10 **nicht bestanden**; End-to-End-Erfolg weiterhin ausstehend.

### FIX-8 Runtime-Verifikation (ohne HW-Lauf), 2026-04-27

- **Nachweis Runtime-Codepfad:** laufender Dienst startet aus `/opt/setuphelfer/backend` (`uvicorn app:app`), Environment mit `PI_INSTALLER_DIR=/opt/setuphelfer`.
- **Nachweis Ursache R10:** Runtime unter `/opt` war nicht durchgaengig auf FIX-7-Stand; zusaetzlich nutzte `modules.storage_detection.validate_backup_target()` einen eigenen Mount-Entscheidungspfad und konnte dadurch weiterhin im aktiven Backup-Target-Gate blockieren.
- **Direkter Runtime-Smoke im Dienst-Venv:** `resolve_mount_source_for_path('/mnt/setuphelfer/backups/test-run')` => `resolved_source=/dev/sda4`, `fstype=ext4`; `validate_write_target(...)` => `OK`.
- **Code-Fix:** `safe_device` robustifiziert (nested `findmnt -R`, automount-trigger retry, lsblk-Fallback bei `PrivateDevices`), `storage_detection.validate_backup_target()` auf `resolve_mount_source_for_path()` umgestellt.
- **Status:** Kein HW-Erfolg behauptet; R11 ist nach dieser Runtime-Konsolidierung sinnvoll erneut pruefbar.

### HW1-01 Repeat-Lauf (EVID-2026-HW1-R11), 2026-04-27

- **outcome:** `success` (voller End-to-End: Backup, Verify deep, Restore Preview; keine Abbruchregel ausgeloest).
- **Pre-Check:** wie Vorgabe (`GET /api/system/service-conflicts` ohne Blocker, `/api/version` 1.5.0.0, Ziel ext4 mit `/dev/sda4`, `root:setuphelfer` + `drwxrws---` auf `test-run` und `test-data`, `SETUPHELFER_DATA_BACKUP_SOURCES=/mnt/setuphelfer/test-data`, Schreibprobe `_probe_r11`).
- **Backup:** `POST /api/backup/create` mit `backup_dir=/mnt/setuphelfer/backups/test-run`, `type=data`, `target=local` → `status=success`, `code=backup.success`, Archiv `pi-backup-data-20260427_213058.tar.gz`; keine Codes `backup.path_invalid`, `STORAGE-PROTECTION-*`, `backup.sudo_required`, `backup.sudo_blocked_by_nnp`, `backup.source_permission_denied`. Tar-Inhalt nur unter `mnt/setuphelfer/test-data/` plus eingebettetes `MANIFEST.json` (kein `/home`, kein `/opt` im Archiv).
- **Verify:** `POST /api/backup/verify` mit `mode=deep` → `status=success`, `valid=true`, `backup.verify_success`.
- **Restore (Preview):** `POST /api/backup/restore` mit `mode=preview` → `status=success`, Sandbox unter `/tmp/setuphelfer-restore-test/...`, `blocked_entries=[]`.
- **confirmed_root_cause (Erfolgs-Linie):** `resolved – unified safe_device + storage_detection + automount fix + explicit data source`.
- **Bewertung:** **HW1-01 ist in R11 nach der strengen SUCCESS-Definition bestanden** (externe ext4-NVMe, nur `type=data`, nur konfigurierte Testdatenquelle).

### HW1-02 Repeat-Lauf (EVID-2026-HW1-R12), 2026-04-27

- **outcome:** `success` (verschluesseltes Daten-Backup inkl. Verify deep, Restore Preview, saubere Negativtests).
- **Pre-Check:** identisch R11 (Konfliktfreiheit, Version 1.5.0.0, ext4 `/dev/sda4`, Rechte `root:setuphelfer`, Testdatenquelle per ENV, Schreibprobe).
- **Backup:** `POST /api/backup/create` mit `encryption: true`, `password: TEST-HW1-KEY-01` (API mappt auf `encryption_method`/`encryption_key`, Default **gpg**) → `backup.success`, `backup_file` endet auf `.tar.gz.gpg`, `encrypted: true`. Keine `STORAGE-PROTECTION-*` / sudo-Fehler im Erfolgslauf.
- **Verify (deep):** `POST /api/backup/verify` mit `file`, `mode: deep`, korrektem `password` → `backup.verify_success`, `valid: true`, `encrypted: true`.
- **Restore (Preview):** `POST /api/backup/restore` mit `file`, `mode: preview`, korrektem Passwort → `backup.restore_preview_ok`, `preview_dir` unter `/tmp/setuphelfer-restore-test/...`.
- **Negativtest:** falsches Passwort `FALSCH` → Verify `backup.verify_decrypt_failed`, Restore `backup.restore_decrypt_failed`, jeweils `status: error`, kein stiller Erfolg, kein Server-Crash.
- **Technische Nacharbeit (Repo/Runtime):** GPG-Unterprozesse nutzen beschreibbares `GNUPGHOME` (Default `/tmp/setuphelfer-gnupg`), damit Dienste ohne schreibbares User-Home verschluesseln; Verify setzt `BackupModule.run_command`; Restore entschluesselt temporaer vor `tar`-Analyse/-Extraktion; Aliase `file`/`password` fuer Verify/Restore.
- **Bewertung:** **HW1-02 in R12 nach strenger SUCCESS-Definition bestanden.**

### HW1-03 (EVID-2026-HW1-03), 2026-04-27 — kontrollierte Negativtests

Voraussetzungen: HW1-01/HW1-02 gruen; externe ext4 unter `/mnt/setuphelfer/backups/test-run`; Quelle `SETUPHELFER_DATA_BACKUP_SOURCES=/mnt/setuphelfer/test-data`; kein Pi/USB/SD; keine echten `/home`-Daten.

| Testfall | Erwartung | Ist-Code / Signal | Diagnose-ID | bestanden |
|----------|-----------|-------------------|-------------|-------------|
| A fehlendes MANIFEST | `backup.failed_manifest_missing`, kein 500 | `backup.failed_manifest_missing`, `status=error` | BACKUP-MANIFEST-001 | ja |
| B Hash-/Integritaet | `backup.verify_integrity_failed`, kein stiller Erfolg | `backup.verify_integrity_failed` | BACKUP-HASH-003 | ja |
| C beschaedigtes Archiv (trunc.) | Archiv-/Gzip-Fehler, deterministisch | `backup.verify_archive_unreadable` | BACKUP-ARCHIVE-002 | ja |
| D nicht erlaubtes Ziel `/media/...` | STORAGE-PROTECTION, kein Schreibversuch | `backup.path_invalid`, Reason `STORAGE-PROTECTION-005` | STORAGE-PROTECTION-005 | ja |
| E Ziel nicht beschreibbar | PERM/OWNER, kein sudo-Workaround | `backup.backup_target_not_writable`, `diagnosis_id` PERM-GROUP-008 | PERM-GROUP-008 | ja |
| F Restore Path-Traversal | Preview blockiert, keine Sandbox-Umgehung | `backup.restore_blocked_entries`, Member `../../../tmp/...` | RESTORE-PATH-004 | ja |

**Technische Nacharbeit (Repo):** `POST /api/backup/verify` mit `mode=deep` auf unverschluesselte `.tar.gz` nutzt `modules.backup_verify.verify_deep` (Manifest + SHA-256); `_analyze_tar_members` erkennt `..`-Segmente korrekt (kein `lstrip("./")`-Kollaps); Restore-Block liefert `details.diagnosis_id`; Ziel-Schreibprobe mappt EACCES auf PERM-GROUP-008.

**Bewertung:** **HW1-03 nach SUCCESS-Definition bestanden** (alle Negativfaelle deterministisch, keine 500er, keine stillen Erfolgsmeldungen auf den geprueften Pfaden).

### HW1-04 (EVID-2026-HW1-04), 2026-04-27 — Restore-Preview und Zielvalidierung

Voraussetzungen: wie HW1-01 R11/R12 (Konfliktfreiheit, Version 1.5.0.0, ext4 unter `/mnt/setuphelfer/backups/test-run`, `SETUPHELFER_DATA_BACKUP_SOURCES=/mnt/setuphelfer/test-data` im Dienst-Environment).

| Phase | Erwartung | Ergebnis |
|-------|-----------|----------|
| 0 Pre-Check | `conflicts=[]`, Version, ext4, Testdaten, ENV | gruen |
| 1 Baseline | `backup.success`, Archiv unter test-run | `pi-backup-data-20260427_221317.tar.gz` |
| 2 Verify deep | `backup.verify_success` | `valid=true`, 4 Eintraege inkl. MANIFEST |
| 3 Restore preview | `backup.restore_preview_ok`, keine `blocked_entries` | OK; `preview_dir` unter Dienst-`PrivateTmp` |
| 3 Inhalt | README `fixture`, sample `{"ok":true}`, MANIFEST plausibel | per `tar -xOzf` aus Archiv verifiziert |
| 4A Ziel /media | STORAGE-PROTECTION | `backup.path_invalid`, Reason **005** |
| 4B Ziel nicht beschreibbar | PERM-008 / not writable | `backup.backup_target_not_writable`, `diagnosis_id` **PERM-GROUP-008** |
| 4C Traversal-Archiv | RESTORE-004 | `backup.restore_blocked_entries`, Member `../../../tmp/...` |

**DOC-SYNC-Check:** keine neuen API-Codes; Matcher/i18n fuer genutzte IDs bereits aus DOC-SYNC-1; optional FAQ-Hinweis **PrivateTmp** vs. manuelles `ls` auf `preview_dir`.

**Bewertung:** **HW1-04 nach SUCCESS-Definition bestanden.**

### HW1-05 (EVID-2026-HW1-05), 2026-04-27 — Restore-Verhalten, Grenzen, Sicherheit (ohne Root-Restore)

Scope: nur Analyse/Preview/Zielvalidierung; **kein** produktiver Restore auf `/`.

| Phase | Erwartung | Ergebnis |
|-------|-----------|----------|
| 0 Pre-Check | conflicts leer, Version 1.5.0.0, ext4, Source aktiv, Port korrekt | gruen |
| 1 Backup-Auswahl | gueltiges Backup mit verify deep success | bestehendes Backup `pi-backup-data-20260427_221317.tar.gz`, verify `backup.verify_success` |
| 2 Preview Baseline | `backup.restore_preview_ok`, keine `blocked_entries` | success, `blocked_entries=[]` |
| 3 Preview-Analyse | plausible counts, keine `/etc` `/root` `/opt` Pfade | nur `mnt/setuphelfer/test-data/*` + `MANIFEST.json` |
| 4 PrivateTmp | `preview_dir` nicht im User-`/tmp` sichtbar | bestaetigt, erwartete Service-Isolation |
| 5A Ziel gueltig | Preview unter gueltigem Backup-Pfad | success |
| 5B Ziel `/media` | STORAGE-PROTECTION-005 | `backup.path_invalid` mit Reason `STORAGE-PROTECTION-005` |
| 5C Ziel nicht beschreibbar | PERM-Blockade | `backup.backup_target_not_writable`, `diagnosis_id=PERM-GROUP-008` |
| 5D Traversal-Archiv | RESTORE-PATH-004 | `backup.restore_blocked_entries`, `diagnosis_id=RESTORE-PATH-004` |
| 6 Risikoanalyse (simuliert) | potenzielle Überschreibpfade ohne echten Restore | nur `/mnt/setuphelfer/test-data/*`, keine Root-Systempfade |

**Bewertung:** **HW1-05 nach SUCCESS-Definition bestanden** (stabile Preview, korrekte Analyse, deterministische Zielblockaden, keine 500er, kein unkontrolliertes Schreibziel).

### FIX-9 API-Consistency (vor HW1-06)

- `GET /api/backup/list` harmonisiert auf read-only Mount-Validierung mit `resolve_mount_source_for_path`; keine unnötige Write-Probe mehr beim Listen.
- Fehlerdetails bei `backup.path_invalid` aus List enthalten jetzt `mount_source_seen`, `resolved_source`, `fstype`, `target`, `diagnosis_id`.
- `POST /api/backup/create` (`type=data`) gibt Source-Planung auch im Erfolgspfad zurück (`selected_sources`, `skipped_sources`, `required_sources`, `optional_sources`).
- `POST /api/backup/restore` (`mode=preview`) liefert PrivateTmp-Kontext (`private_tmp_isolation`, `preview_dir_visibility_note`, `service_private_tmp_hint`).

### SERVICE-SMOKE vor HW1-06 (2026-04-28)

- Ziel: Live-Erreichbarkeit vor HW1-06 und FIX-9-Endpunkte (`/api/system/service-conflicts`, `/api/backup/list`) prüfen.
- Ergebnis: **failed / blockiert** trotz aktivem Dienst und funktionierendem `/api/version` (`1.5.0.0`).
- Beobachtung: `curl --max-time 5` auf `service-conflicts`/`backup/list` lief wiederholt in Timeouts; nach Restart meldet systemd beim Stop `stop-sigterm timed out` und SIGKILL.
- Portzustand: Listener auf `127.0.0.1:8000` vorhanden, zusätzlich mehrere `CLOSE_WAIT`-Sockets am Backend-Prozess.
- Evidence: `EVID-2026-HW1-FIX9-SMOKE-FAIL`.
- Bewertung: **HW1-06 bis zur Stabilisierung der Live-Responsiveness blockiert** (kein funktionaler FIX-9-Widerspruch im Code, aber Runtime-Smokegate nicht grün).

### FIX-10 backup/list stability (2026-04-28)

- Ziel: `/api/backup/list` darf den Worker nicht blockieren und muss innerhalb kurzer Grenzen antworten.
- Codeanpassungen: read-only List-Pfad, Pfadvalidierung ohne Write-Probe, Validierung/Scan in `to_thread + wait_for` mit Timeout, strukturierter Fehler `backup.list_timeout`.
- Ergebnis im Live-Smoke: **inkonsistent** — `api/version` und `api/system/service-conflicts` stabil, `api/backup/list` jedoch weiterhin intermittierend mit Client-Timeout.
- `/media`-Pfad liefert bei erfolgreicher Verarbeitung weiterhin deterministisch `backup.path_invalid` + `STORAGE-PROTECTION-005`.
- Evidence: `EVID-2026-HW1-FIX10-BACKUP-LIST-STABILITY`.
- Bewertung: **Service-Smoke nicht vollständig grün, HW1-06 bleibt blockiert**.

### FIX-11 backup/list decouple (2026-04-28)

- Ziel: `GET /api/backup/list` vollständig von potenziell blockierendem Mount-/Directory-Scan im Requestpfad entkoppeln.
- Codeanpassungen:
  - List-Endpoint liest primär aus lokalem `backup-index.json` im State-Pfad.
  - Kein `glob`/`scandir` im Requestpfad; nur kurze optionale `quick_stat`-Checks je Indexeintrag.
  - Bei fehlendem Index: deterministisches `success` mit leerer Liste und `index_available=false`.
  - `/media`/`/run/media` weiterhin sofort blockiert (`backup.path_invalid`, `STORAGE-PROTECTION-005`), ohne Scan.
  - Erfolgreiche Backups schreiben/aktualisieren Index-Metadaten (`backup_file`, `created_at`, `encrypted`, `size_bytes`, `type`, `target`, `source_summary`, `manifest_present`, `verification_status`, `storage_path`).
- Unit-Tests:
  - `backend/tests/test_api_consistency_fix9_v1.py`
  - `backend/tests/test_backup_list_decouple_fix11_v1.py`
  - Ergebnis: `Ran 8 tests ... OK`.
- Live-Smoke nach Deploy:
  - `/api/version` -> `success`, Version `1.5.0.0`
  - `/api/system/service-conflicts` -> `success`, `conflicts=[]`
  - `/api/backup/list?backup_dir=/mnt/setuphelfer/backups/test-run` -> `success`, kein Timeout, `index_available=false`
  - `/api/backup/list?backup_dir=/media/volker/INTENSO` -> `backup.path_invalid` + `STORAGE-PROTECTION-005`
  - `systemctl restart setuphelfer-backend` -> sauberer Restart, Service `active (running)`, kein SIGKILL im sichtbaren Restart-Fenster.
- Bewertung: **backup/list-Smoke-Gate für HW1-06-Blocker ist grün**; die eigentliche HW1-06-Freigabe bleibt an die restlichen HW1-06-Kriterien gebunden.

### HW-EXEC-1-06 (EVID-2026-HW1-06), 2026-04-28 — kontrollierter Restore auf Zielpfad

- **outcome:** `aborted_precheck` (regelkonformer Abbruch in Phase 0; kein Restore gestartet).
- **Pre-Check Ergebnisse:**
  - `GET /api/system/service-conflicts` -> `success`, `conflicts=[]`, `should_block_start=false` (pass)
  - `GET /api/version` -> `1.5.0.0` (pass)
  - `GET /api/backup/list?backup_dir=/mnt/setuphelfer/backups/test-run` -> `success`, kein Timeout (pass)
  - `findmnt /mnt/setuphelfer/backups/test-run` -> `SOURCE=systemd-1`, `FSTYPE=autofs` (**fail**, erwartet ext4)
  - `ls -ld /mnt/setuphelfer/backups/test-run` -> `root:root drwxr-xr-x` (**fail**, erwartet `root:setuphelfer drwxrws---`)
  - `ls -ld /mnt/setuphelfer/test-data` -> `root:setuphelfer drwxrws---` (pass)
  - `ls -ld /mnt/setuphelfer/restore-target` -> Pfad fehlt (**fail**)
- **Folge gemäß Testregel:** ABORT + Evidence; **kein** Baseline-Backup, **kein** Verify, **kein** Restore, **keine** Negativtests A-C.
- **Diagnose/Root-Cause:** Umgebung nicht im geforderten Restore-Zielzustand (Owner/Mode/Mount-Layer), dadurch kontrollierter Restore-Test nicht belastbar durchführbar.
- **Evidence:** `data/diagnostics/evidence/EVID-2026-HW1-06.json`.
- **Bewertung:** **HW1-06 nicht bestanden (aborted in Pre-Check)**.

### HW1-06-ENV-BASELINE (EVID-2026-HW1-06-ENV-BASELINE), 2026-04-28

- Ziel: Mount- und Restore-Zielbasis fuer HW1-06 stabil herstellen (ohne Backup/Verify/Restore).
- Ist-Aufnahme:
  - `findmnt /mnt/setuphelfer/backups/test-run` und `findmnt -R ...` liefen in Timeout.
  - `/proc/mounts` zeigte weiterhin nur `systemd-1 ... autofs` fuer `test-run`.
  - `fstab`-Eintrag vorhanden: `UUID=a8cd880d-ba96-49a5-b5cd-135cd7f020b0 ... ext4 ... x-systemd.automount`.
  - `restore-target` nicht vorhanden.
- Phase 1 (Mount herstellen):
  - Automount-Trigger (`ls ...`) -> Timeout.
  - Re-Check mit `findmnt` -> Timeout.
  - `sudo systemctl daemon-reload` + `sudo mount /mnt/setuphelfer/backups/test-run` -> Mount-Befehl Exit 0, aber ext4-Zustand danach weiterhin nicht bestaetigbar (`findmnt` erneut Timeout, `/proc/mounts` weiter autofs).
- Regelanwendung:
  - Gemäß Vorgabe bei Mount-Fehlschlag: **keine weiteren Aktionen**.
  - Daher **keine** Rechteaenderung auf `test-run`, **kein** Anlegen von `/mnt/setuphelfer/restore-target`, **keine** Schreibtests, **kein** API-Smoke in dieser Phase.
- **Evidence:** `data/diagnostics/evidence/EVID-2026-HW1-06-ENV-BASELINE.json`.
- **Bewertung:** **HW1-06 bleibt gesperrt**, ENV-Baseline-Gates nicht gruen (ext4-Zustand/Path-Access nicht stabil verifizierbar).

### NVME-REBUILD-HW1 (EVID-2026-NVME-REBUILD), 2026-04-28

- Ziel: externe NVMe fuer HW1 neu strukturieren (klare Linux/Windows-Trennung, keine autofs-Abhaengigkeit, reproduzierbare Mount-Basis).
- Sicher identifiziertes Geraet: `/dev/sda` (USB, `Samsung SSD 970 EVO Plus 2TB`), interne NVMe (`/dev/nvme0n1`, `/dev/nvme1n1`) unveraendert.
- Durchgefuehrte Schritte:
  - GPT neu erstellt auf `/dev/sda`.
  - Partitionen erstellt: `sda1` (0-50%), `sda2` (50-100%).
  - Dateisysteme erstellt:
    - `/dev/sda1` -> ext4, UUID `adbd53e5-26fd-4723-b0f1-1880dbaa2719`, Label `setuphelfer-back` (mkfs-kuerzung)
    - `/dev/sda2` -> ntfs, UUID `01BDA42D54D84B41`, Label `windows-backup`
  - Mountpoints:
    - `/mnt/setuphelfer/backups`
    - `/mnt/windows-backup`
  - `/etc/fstab` ohne automount/autofs-Eintrag:
    - `UUID=adbd53e5-26fd-4723-b0f1-1880dbaa2719 /mnt/setuphelfer/backups ext4 defaults,nofail 0 2`
    - `UUID=01BDA42D54D84B41 /mnt/windows-backup ntfs defaults,nofail 0 2`
  - `systemctl daemon-reload` + `mount -a` erfolgreich.
- Validierung:
  - `findmnt /mnt/setuphelfer/backups` -> `/dev/sda1` `ext4`
  - `findmnt /mnt/windows-backup` -> `/dev/sda2` `fuseblk`
  - kein autofs-Layer auf den neuen Zielmounts.
- Setuphelfer-Rechte + Test:
  - `/mnt/setuphelfer/backups` auf `root:setuphelfer` und `drwxrws---` gesetzt.
  - Schreibtest `touch /mnt/setuphelfer/backups/_nvme_test` erfolgreich.
- API-Smoke:
  - `/api/version` -> `1.5.0.0`
  - `/api/system/service-conflicts` -> `conflicts=[]`
  - `/api/backup/list?backup_dir=/mnt/setuphelfer/backups` -> `success`, kein Timeout.
- Evidence: `data/diagnostics/evidence/EVID-2026-NVME-REBUILD.json`.
- Bewertung: **NVMe-Basis ist jetzt stabil fuer HW1** (Storage-/Mount-Gates gruen).

### HW-EXEC-1-06 Retry nach NVME-Rebuild (EVID-2026-HW1-06), 2026-04-28

- **Pre-Check:** gruen (`/api/version=1.5.0.0`, `service-conflicts` ohne Blocker, `/mnt/setuphelfer/backups` auf `/dev/sda1 ext4`, Rechte `root:setuphelfer drwxrws---`, `restore-target` vorhanden, `backup/list` ohne Timeout).
- **Baseline-Backup:** `POST /api/backup/create` (`type=data`, `target=local`, `backup_dir=/mnt/setuphelfer/backups`) -> `backup.success`, Datei `pi-backup-data-20260428_224600.tar.gz`, `selected_sources=['/mnt/setuphelfer/test-data']`.
- **Verify deep:** `POST /api/backup/verify` -> `backup.verify_success`, `valid=true`.
- **Restore-Aufruf (kontrollierter Zielpfad):** `POST /api/backup/restore` mit `mode=restore`, `target_dir=/mnt/setuphelfer/restore-target` lieferte **`mode=preview`** und `code=backup.restore_preview_ok` statt eines echten targetgebundenen Restore-Laufs.
- **Inhaltsvalidierung:** Archivinhalt korrekt (`MANIFEST.json`, `README.txt`, `sample.json`), `README`/`sample.json` stimmen mit Quelle unter `/mnt/setuphelfer/test-data` überein.
- **Negativtests A-C (media, non-writable, root):** alle lieferten ebenfalls `backup.restore_preview_ok` statt erwarteter Blockaden (`backup.path_invalid`/`STORAGE-PROTECTION-005`, `PERM-GROUP-008`, Root-Gate).
- **Bewertung:** **HW1-06 nicht bestanden**; Backup/Verify sind stabil, aber Restore-Zielvalidierung ist im aktuellen API-Verhalten nicht nachweisbar, weil `target_dir` im angefragten Restore-Pfad effektiv nicht erzwungen wird.

### HW-EXEC-1-06-R2 (EVID-2026-HW1-06-R2), 2026-04-28 — Abschluss nach FIX-12

- **Pre-Check:** vollständig grün
  - `/api/system/service-conflicts` -> `conflicts=[]`, `should_block_start=false`
  - `/api/version` -> `1.5.0.0`
  - `/api/backup/list?backup_dir=/mnt/setuphelfer/backups` -> `backup.list_ok`, kein Timeout
  - Rechte: `/mnt/setuphelfer/backups`, `/mnt/setuphelfer/restore-target`, `/mnt/setuphelfer/test-data` jeweils `root:setuphelfer drwxrws---`
- **Phase 1 (Backup):**
  - `POST /api/backup/create` (`type=data`, `target=local`, `backup_dir=/mnt/setuphelfer/backups`)
  - Ergebnis: `backup.success`, Datei `pi-backup-data-20260428_230201.tar.gz`, `selected_sources=['/mnt/setuphelfer/test-data']`
- **Phase 2 (Verify deep):**
  - Ergebnis: `backup.verify_success`, `valid=true`
- **Phase 3 (Preview):**
  - Ergebnis: `backup.restore_preview_ok`, `blocked_entries=[]`
- **Phase 4 (echter Restore):**
  - Ziel: `/mnt/setuphelfer/restore-target/hw1-06-r2`
  - Ergebnis: `backup.restore_success`
  - Dateien real im Ziel vorhanden (`MANIFEST.json`, `README.txt`, `sample.json` unter restore tree)
- **Phase 5 (Inhaltsvalidierung):**
  - `README.txt` vorhanden und inhaltlich gleich zur Quelle
  - `sample.json` vorhanden und inhaltlich gleich zur Quelle (`{"ok": true}`)
  - `MANIFEST.json` vorhanden
  - keine unerwarteten Systempfade, keine Einträge außerhalb `target_dir`
- **Phase 6 (Negativtests):**
  - A `/media/volker/INTENSO` -> `backup.restore_target_invalid`, `diagnosis_id=STORAGE-PROTECTION-005`
  - B `/mnt/setuphelfer/restore-nowrite` (0555) -> `backup.restore_not_writable`, `diagnosis_id=PERM-GROUP-008`
  - C `/` -> `backup.restore_target_invalid`, `diagnosis_id=RESTORE-RUNTIME-006`
- **Evidence:** `data/diagnostics/evidence/EVID-2026-HW1-06-R2.json`
- **Bewertung:** **HW1-06 bestanden** (alle Success-Kriterien erfüllt, keine 500er).

### HW-EXEC-1-07 (EVID-2026-HW1-07), 2026-04-28 — Reproduzierbarkeitslauf

- Ziel: erfolgreiche NVMe-Recovery-Kette aus HW1-06 erneut ohne zusätzliche Fixes reproduzieren.
- **Pre-Check:** vollständig grün
  - `service-conflicts` konfliktfrei
  - Version `1.5.0.0`
  - `backup/list` auf `/mnt/setuphelfer/backups` erfolgreich, kein Timeout
  - Rechte korrekt auf Backup-/Restore-/Testdatenpfad (`root:setuphelfer`, `drwxrws---`)
- **Backup:** `backup.success` mit Datei `pi-backup-data-20260428_230633.tar.gz`, `selected_sources=['/mnt/setuphelfer/test-data']`
- **Verify deep:** `backup.verify_success`, `valid=true`
- **Preview:** `backup.restore_preview_ok`, `blocked_entries=[]`
- **Restore:** `backup.restore_success` auf `/mnt/setuphelfer/restore-target/hw1-07`
- **Inhaltsvalidierung:** `README.txt`, `sample.json`, `MANIFEST.json` vorhanden und inhaltlich konsistent zur Quelle; keine Einträge außerhalb `target_dir`, keine unerwarteten Systempfade.
- **Abweichung zu HW1-06:** keine funktionale Abweichung; die identische Kette lief erneut stabil durch.
- **Evidence:** `data/diagnostics/evidence/EVID-2026-HW1-07.json`
- **Bewertung:** **Reproduzierbarkeit bestätigt**.

### HW1-01 Repeat-Lauf (EVID-2026-HW1-R01), 2026-04-24

- **outcome:** `failed` (Abbruch nach Phase 0 laut Anweisung; kein vollstaendiger Backup/Verify/Preview-Lauf).
- **Symptome:** `touch` auf `/mnt/setuphelfer/backups/test-run` in der genutzten Shell mit *Keine Berechtigung*; `id -G` ohne `1001` (setuphelfer); mit `sg setuphelfer` war Schreiben am Mountpunkt moeglich. ext4-Mount und `root:setuphelfer` / `0770` auf dem Einhaengepunkt waren konsistent.
- **Diagnose:** `PERM-GROUP-008` (suspected/confirmed Kontext: fehlende aktive Supplementary Group in der Pruefshell, nicht falsches Dateisystem).
- **Besonderheiten:** Auf Port 8000 lief ein anderes PI-Installer-Backend (`/opt/pi-installer`); `setuphelfer-backend.service` war inactive und die installierte Unit wich vom Repo ab (kein `ReadWritePaths=/mnt/setuphelfer`, kein `SupplementaryGroups=setuphelfer`). Fuer einen belastbaren HW1-01-Repeat: Session/Unit bereinigen, Phase 0 strikt mit gueltigem Gruppenkontext wiederholen, dann Produkttests.

### HW1-01 Repeat-Lauf (EVID-2026-HW1-R02), 2026-04-24 (RUN)

- **outcome:** `failed` (kein Backup-Archiv; Verify/Preview nicht gestartet).
- **Symptome:** Phase 0 in **Login-Shell** (`su - volker`) bestanden (`id -G` mit setuphelfer, `touch` OK). `POST /api/backup/create` → `backup.sudo_required`. `setuphelfer.service` (UI) weiterhin Abbruch bei `npm run build` (Exit 159).
- **Diagnose:** **`SYSTEMD-NNP-031`** — `sudo -n true` im Backend-Prozess schlaegt unter `NoNewPrivileges=true` fehl; die API brach wegen **pauschalem sudo-Gate** vor dem Tar ab (nicht wegen des Tar-Laufs selbst).
- **Nacharbeit (FIX-2-SUDO-GATE, Code):** `/api/backup/create` fuehrt fuer **type=data** und **target=local** nach validiertem Ziel unter der Storage-Allowlist **kein** `sudo -n true` mehr aus und nutzt **`os.makedirs`** statt `sudo mkdir`. Erneuter HW-Lauf moeglich als **R03** (Evidence/Matrix separat).
- **Besonderheiten:** Backend auf 127.0.0.1:8000 aktiv (setuphelfer-backend). Strenges UI-SUCCESS kann weiter an `setuphelfer.service`/Vite haengen; API-Pfad fuer Datenbackup ist entblockt.

### HW1-01 Repeat-Lauf (EVID-2026-HW1-R03), 2026-04-24

- **outcome:** `failed` (kein E2E SUCCESS).
- **Unterschied zu R01:** R01 scheiterte an Session ohne aktive Gruppe `setuphelfer` in der Pruefshell; R03 nutzte Login-Shell mit GID 1001, scheiterte stattdessen am **Zielzustand** (Verzeichnis nicht beschreibbar, kein ext4-Mount).
- **Unterschied zu R02:** R02 traf **setuphelfer-backend** mit NNP und pauschalem sudo-Gate (vor FIX-2); R03 traf auf dem Host **pi-installer** auf Port **8000** (`/api/version` **1.3.4.15**), **setuphelfer-backend** **inactive** — kein FIX-2 auf dem Listener, zusaetzlich Pre-Check **touch** fehlgeschlagen.
- **Symptome:** `ls -ld` → `drwxr-xr-x root root`; `findmnt` ohne Eintrag fuer `test-run`; `touch _probe_r03` EACCES; Backup-POST weiterhin sudo-Pflicht auf dem Fremd-Backend.
- **Diagnose:** `PERM-GROUP-008` / `OWNER-MODE-023` (suspected) — Umgebung nicht HW1-tauglich; nicht „FIX-2 fehlerhaft“.
- **finale Bewertung:** HW1-01 ist **nach** bereitgestelltem FIX-2 im **Quell-Repo** erneut **ausfuehrbar**, sobald **(a)** ext4 korrekt unter `.../test-run` haengt **root:setuphelfer** **0770**, **(b)** **setuphelfer-backend** (Build mit FIX-2) **allein** auf **8000** laeuft. Auf dem geprueften Host war R03 **kein** belastbarer FIX-2-Verifikationslauf.

---

## DEPLOY-FIX-SETUPHELFER-1 (Laptop-Umgebung, 2026-04-25)

- **Altinstallation identifiziert:** `pi-installer.service` lief aktiv, Port `8000` war durch `/opt/pi-installer` belegt, `/api/version` meldete `1.3.4.15`.
- **Stilllegung Altstack:** `pi-installer.service` gestoppt und deaktiviert (`disabled`/`inactive`).
- **Deploy Neu-Stand:** aktueller Repo-Stand nach `/opt/setuphelfer` synchronisiert (keine aktive Runtime mehr unter `/opt/pi-installer`).
- **Systemd/Port:** `setuphelfer-backend.service` aktiv, `NoNewPrivileges=true`, `SupplementaryGroups=setuphelfer`, `ReadWritePaths` inkl. `/mnt` und `/mnt/setuphelfer` (Drop-in); Port `8000` belegt durch `setuphelfer-backend` (`python3`, User `volker`, localhost).
- **Version/FIX-2 verifiziert:** `/api/version` liefert `1.5.0.0`; in `/opt/setuphelfer/backend/app.py` sind `_backup_create_needs_sudo_precheck` und `backup.sudo_blocked_by_nnp` vorhanden.
- **Evidence:** `EVID-2026-HW1-ENV-DEPLOY-01` (Umgebungs-Deploy).
- **Gate fuer HW1-01 R04:** **noch nicht freigegeben**, da `/mnt/setuphelfer/backups/test-run` aktuell **nicht** als ext4-Mount aktiv ist und Owner/Mode am Zielpfad nicht im erwarteten Zustand (`root:setuphelfer`, `0770`) liegen.

---

## ENV-FIX-HW1-R04-MOUNT (Laptop-Umgebung, 2026-04-25)

- **Verwendete Partition:** `/dev/sda4`
- **Dateisystem:** `ext4`
- **Mountpoint:** `/mnt/setuphelfer/backups/test-run`
- **findmnt:** `SOURCE=/dev/sda4`, `FSTYPE=ext4`
- **Owner/Mode:** `drwxrws--- root:setuphelfer` (entspricht `0770`, setgid-Bit aktiv)
- **Login-Shell-Schreibtest:** `id -G` enthaelt `1001 (setuphelfer)`; `touch /mnt/setuphelfer/backups/test-run/_r04_mount_probe` erfolgreich
- **API/Port:** Port `8000` weiterhin durch `setuphelfer-backend` belegt; `/api/version` = `1.5.0.0`
- **Freigabestatus HW1-01 R04:** **freigegeben** (Mount-/Rechte-/Runtime-Voraussetzungen fuer den Testlauf sind erfuellt; eigentlicher HW-Lauf noch ausstehend)

---

## HW1-01 Repeat-Lauf (EVID-2026-HW1-R04), 2026-04-25

- **outcome:** `failed`
- **Phase-0:** erfolgreich (Login-Shell mit `setuphelfer`, Schreibprobe auf `/mnt/setuphelfer/backups/test-run`, API-Version `1.5.0.0`)
- **Backup:** `POST /api/backup/create` mit `type=data`, `target=local` lief ohne `backup.sudo_required`/`backup.sudo_blocked_by_nnp`, endete aber nach langem Tar-Lauf mit `backup.failed`.
- **Fehlersignal:** API-`results` enthielt `tar ... Keine Berechtigung` (u. a. fuer `/home` und `/opt/containerd`) bei Archivpfad `pi-backup-data-20260425_084413.tar.gz`.
- **Verify/Preview:** nicht gestartet, da Backup nicht erfolgreich abgeschlossen wurde.
- **Diagnoseeinschaetzung:** `BACKUP-SOURCE-PERM-032` (suspected) — Data-Scope enthielt nicht lesbare/systemnahe Quellen; Zielpfad war korrekt, Quelle nicht passend für nicht-privilegierten `type=data`.

### Vergleich R01–R04 (Kurz)

- **R01:** fehlende aktive Gruppe in Pruefshell (`PERM-GROUP-008`).
- **R02:** pauschales sudo-Gate vor Tar (`SYSTEMD-NNP-031`), vor FIX-2.
- **R03:** falscher Zielzustand + falscher Listener (pi-installer statt setuphelfer-backend).
- **R04:** ENV + FIX-2 korrekt, aber Data-Tar scheitert an Quellpfad-Leserechten.

**Finale Bewertung nach R04:** Fix-2 (Sudo-Gate) wirkt, aber HW1-01 ist noch **nicht stabil erfolgreich**, da der Data-Backup-Lauf im aktuellen Dienstkontext an Quell-Leserechten scheitert.

**Nacharbeit FIX-3 (Data-Source-Scope):** `type=data` wurde im Code auf nicht-privilegierte Quellen begrenzt (kein pauschales `/opt`, kein Container-Runtime-Scope wie `/opt/containerd`), inkl. strukturierter API-Antwort `backup.source_permission_denied` mit `diagnosis_id=BACKUP-SOURCE-PERM-032`. R05 ist damit sinnvoll erneut ausführbar.

### Übersicht R01-R04

| Run | Outcome | Root Cause (kurz) | Diagnosis-ID(s) | Fix | Status für R05 |
|-----|---------|-------------------|-----------------|-----|----------------|
| R01 | failed | Session/Gruppe `setuphelfer` nicht wirksam in Prüfshell | `PERM-GROUP-008` | ENV-/Session-Fix | vorbereitet |
| R02 | failed | Pauschales sudo-Gate vor Tar unter `NoNewPrivileges` | `SYSTEMD-NNP-031` | FIX-2 (`data/local` ohne sudo-Gate) | adressiert |
| R03 | failed | Falscher Zielzustand + falscher Dienst auf Port 8000 (Altinstallation) | `OWNER-MODE-023`, `PERM-GROUP-008` | DEPLOY-/ENV-Fix | adressiert |
| R04 | failed | Data-Scope zu breit, nicht lesbare Quellen im Tar (`/opt/containerd` etc.) | `BACKUP-SOURCE-PERM-032` (nach FIX-3) | FIX-3 (Data-Scope begrenzt + strukturierter Fehler) | R05 sinnvoll |

## HW1-01 Repeat-Lauf (EVID-2026-HW1-R05), 2026-04-25

- **outcome:** `failed`
- **Phase-0:** vollständig grün (Gruppe, ext4-Mount, Zielrechte, Schreibprobe, API 1.5.0.0, Port 8000 korrekt).
- **Backup:** `POST /api/backup/create` mit `type=data`, `target=local` lief ohne sudo-Gate, endete aber nach **1717 s** erneut mit `backup.failed`.
- **Fehlersignal:** Response enthielt weiterhin `tar ... Keine Berechtigung` auf Quellpfaden, erneut inkl. `/home` und `/opt/containerd`.
- **Verify/Preview:** nicht ausgeführt (harter Abbruch nach fehlgeschlagenem Backup).
- **Diagnoseeinschätzung:** `BACKUP-SOURCE-PERM-032` **confirmed**.
- **Vergleich zu R01-R04:** R05 bestätigt, dass ENV und sudo-Gate stabil sind; der verbleibende Blocker ist weiterhin der **effektive Data-Quellscope im laufenden Runtime-Artefakt**.
- **Finale Bewertung:** HW1-01 ist aktuell **nicht stabil erfolgreich**. Für den nächsten Lauf muss verifiziert werden, dass der laufende Dienst tatsächlich den FIX-3-Scope (ohne pauschales `/opt`) verwendet.

## FIX-4 Runtime-Source-Trace (ohne HW-Lauf), 2026-04-26

- **IST-Analyse bestätigt:** aktives Runtime-Artefakt unter `/opt/setuphelfer/backend/app.py` enthielt im `type=data`-Pfad noch `tar -czf ... /home /var/www /opt` und wich damit vom Repo-FIX-3 ab.
- **Zweiter Source-Pfad gefunden:** zusätzlich nutzte der eingebettete Scheduler-Runner (`_render_backup_runner_script`) für `rtype == "data"` ebenfalls die alte harte Liste.
- **Fix umgesetzt:** `type=data` verwendet jetzt ausschließlich Source-Planning (`_plan_data_backup_sources` bzw. `plan_data_backup_sources` im Runner) mit hartem Ausschluss des gesamten `/opt`-Trees inkl. `/opt/containerd`.
- **Trace/Evidence ergänzt:** strukturierte Runtime-Logs für `selected_sources`, `skipped_sources`, `required_sources`, `optional_sources` plus `effective_tar_command`; API-Details bei `backup.source_permission_denied` enthalten dieselben Quellinformationen.
- **Deploy-Verifikation:** Repo nach `/opt/setuphelfer` synchronisiert, `setuphelfer-backend.service` neu gestartet (`active`), `/api/version` erreichbar (`1.5.0.0`), Runtime-Code enthält FIX-4-Trace und kein `type=data`-Fallback auf `/home /var/www /opt`.
- **Freigabestatus R06:** **freigegeben**, da der identifizierte Runtime-Mismatch behoben und verifiziert ist (ohne Durchführung des eigentlichen HW1-Laufs).

## HW1-01 Repeat-Lauf (EVID-2026-HW1-R06), 2026-04-26

- **outcome:** `failed` (regelkonformer Abbruch in Phase 0 / Pre-Check).
- **Pre-Check:** `id -G` enthielt `1001` (setuphelfer), aber `findmnt /mnt/setuphelfer/backups/test-run` lieferte keinen Mount-Eintrag.
- **Zielpfad-Zustand:** `ls -ld /mnt/setuphelfer/backups/test-run` zeigte `drwxr-xr-x root root` statt erwartet `drwxrws--- root setuphelfer`.
- **Schreibprobe:** `touch /mnt/setuphelfer/backups/test-run/_probe_r06` schlug mit `Keine Berechtigung` fehl.
- **Runtime/API:** `/api/version` war erreichbar (`1.5.0.0`), jedoch wurden **Backup/Verify/Preview nicht gestartet**, da die Vorbedingungen nicht erfüllt waren.
- **Diagnoseeinschätzung:** `OWNER-MODE-023` / `PERM-GROUP-008` (confirmed für diese Ausführung); kein Workaround, kein HW-Fortsetzen.
- **Nächster Schritt für R06-Repeat:** ext4-Mount wiederherstellen und Zielrechte auf `root:setuphelfer` + `0770` setzen, dann Phase 0 erneut grün nachweisen und erst danach End-to-End starten.

## ENV-BASELINE-HW1-PERSISTENT-MOUNT (EVID-2026-HW1-ENV-MOUNT-BASELINE), 2026-04-26

- **Ziel:** stabile, reproduzierbare Mount-/Rechtebasis fuer HW1 herstellen (ohne Backup/Verify/Preview-Lauf).
- **Ursache des instabilen Zustands:** ext4-Testpartition war unter `/media/volker/<uuid>` automounted; der HW1-Pfad `/mnt/setuphelfer/backups/test-run` war dadurch nur ein lokales Verzeichnis mit `root:root 0755`.
- **Verwendete Testpartition:** `/dev/sda4`, `UUID=a8cd880d-ba96-49a5-b5cd-135cd7f020b0`, `FSTYPE=ext4`.
- **Persistenz umgesetzt:** `/etc/fstab` per Backup gesichert (`/etc/fstab.setuphelfer-hw1.bak`) und UUID-Eintrag gesetzt: `UUID=a8cd880d-ba96-49a5-b5cd-135cd7f020b0 /mnt/setuphelfer/backups/test-run ext4 defaults,nofail,x-systemd.automount 0 2`.
- **Finaler Mount-/Rechtezustand:** `findmnt` zeigt `/dev/sda4 -> /mnt/setuphelfer/backups/test-run (ext4)`; `ls -ld` zeigt `drwxrws--- root setuphelfer`; Schreibprobe `_baseline_probe` erfolgreich.
- **Service-/Port/API:** `setuphelfer-backend` aktiv, `SupplementaryGroups=setuphelfer`, `ReadWritePaths` enthält `/mnt/setuphelfer`; Port `8000` durch Backend belegt; `/api/version` = `1.5.0.0`.
- **Freigabestatus für nächsten HW1-Lauf:** **grün/freigegeben**; alle ENV-Gates erfüllt, keine `/media/<user>`-Nutzung für die ext4-Testpartition und keine `/dev/sdX`-Abhängigkeit im persistierten Setup.

## HW1-01 Repeat-Lauf (EVID-2026-HW1-R07), 2026-04-26

- **outcome:** `failed`.
- **Phase-0:** vollständig grün (`findmnt` ext4 auf `/mnt/setuphelfer/backups/test-run`, `root:setuphelfer` + `drwxrws---`, `id -G` mit `setuphelfer`, Schreibprobe `_probe_r07` erfolgreich, Port `8000` korrekt, `/api/version` = `1.5.0.0`).
- **Backup:** `POST /api/backup/create` mit `type=data`, `target=local` brach sofort ab mit `code=backup.error`, Meldung: `Fehler bei der Backup-Erstellung: [Errno 13] Permission denied: '/home/volker'`.
- **Verify/Preview:** nicht gestartet (regelkonform, da Backup nicht erfolgreich).
- **Interpretation:** Kein Hinweis auf `/opt`-/`/opt/containerd`-Regression im Response; der Lauf scheitert früher am Pflicht-Quellpfad (`/home/volker`) im aktiven Service-Kontext.
- **Diagnoseeinschätzung:** `BACKUP-SOURCE-PERM-032` (confirmed für R07-Kontext: nicht lesbare Data-Pflichtquelle).
- **Status HW1-01:** weiterhin **nicht bestanden**; End-to-End-Kette bleibt bis zur Behebung des Quellzugriffs auf `Path.home()` im Dienstkontext blockiert.

## FIX-6 Data-Test-Source Baseline (ohne HW-Lauf), 2026-04-26

- **Ausgangslage:** Nach FIX-5 war der Fehlerpfad korrekt strukturiert (`backup.source_permission_denied`), aber `type=data` blieb auf Service-Home fokussiert und dadurch unter `ProtectHome=yes` nicht HW1-tauglich.
- **Neue Testquelle:** `/mnt/setuphelfer/test-data` eingerichtet mit `root:setuphelfer` und `drwxrws---`, plus kleine nicht-personenbezogene Testdateien (`README.txt`, `sample.json`).
- **Data-Scope-Konfiguration:** systemd Drop-In gesetzt: `Environment="SETUPHELFER_DATA_BACKUP_SOURCES=/mnt/setuphelfer/test-data"`.
- **Service-Kontext unverändert gehärtet:** `ProtectHome=yes`, `NoNewPrivileges=yes`, `ReadWritePaths` inkl. `/mnt/setuphelfer`.
- **Validierung ohne Backup-Lauf:** Source-Plan im Service-Python liefert ausschließlich `includes=['/mnt/setuphelfer/test-data']`, kein `/home/volker`, kein `/opt`.
- **Bewertung:** HW1-01 R09 ist als echter Success-Lauf **vorbereitet**, da eine reproduzierbare nicht-privilegierte Data-Quelle im Dienstkontext verfügbar ist (ohne Abschwächung der Security-Policy).
