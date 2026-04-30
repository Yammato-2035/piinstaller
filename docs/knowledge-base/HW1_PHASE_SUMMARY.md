# Setuphelfer – HW1 Phase Summary

## 1. Ziel der HW1-Phase

Ziel der bisherigen HW1-Phase war der Aufbau einer stabilen, reproduzierbaren Testbasis für Backup, Verify, Restore-Preview, Diagnose, Evidence und Wissensdatenbank auf realer Hardware mit externer ext4-NVMe.

Der Schwerpunkt lag nicht auf schneller Funktion, sondern auf belastbarer Fehleranalyse:

- keine Scheinerfolge
- kein stilles Ignorieren von Fehlern
- keine sudo-Workarounds
- keine unsicheren Schreibziele
- konsequente Evidence-Erfassung
- Rückfluss in Diagnosekatalog, FAQ, i18n und Entwicklerdokumentation

---

## 2. Erreichter Architekturstand

### Zentrale Komponenten

- Backup Engine für `type=data`
- Verify Engine mit Deep-Verify, Manifest und SHA-256
- Restore Preview in Sandbox
- Safe-Device-Schutz gegen falsche Zielgeräte
- Diagnosekatalog mit Matcher-Regeln
- Evidence-System mit strukturierten JSON-Records
- Service-Conflict-Guard gegen parallele Alt-/Neuinstallationen
- Wissensdatenbank und FAQ in DE/EN

### Wichtige Sicherheitsprinzipien

- `Detect != Write`
- Schreibzugriff nur auf explizit erlaubte Ziele
- keine `/media/<user>`-Ziele
- keine automatische Aufnahme von `/home/*`
- keine automatische Aufnahme von `/opt` oder Containerdaten
- kein sudo im normalen `type=data/local`-Pfad
- `ProtectHome` und `NoNewPrivileges` bleiben aktiv

---

## 3. Wesentliche Probleme und Lösungen

| Problem | Erkenntnis | Lösung |
|---|---|---|
| Alte `pi-installer`-Installation belegte Port 8000 | Tests liefen gegen falsche Runtime | Service-Conflict-Guard, Legacy-Service gestoppt/deaktiviert |
| `/media/volker/...` als Ziel | User-Automount ist nicht reproduzierbar und wird blockiert | persistenter UUID-Mount unter `/mnt/setuphelfer/backups/test-run` |
| ext4 falsch mit `gid/umask` gemountet | `gid/umask` ist für ext4 falsch | ext4 ohne Optionen mounten, danach `chown/chmod` |
| `NoNewPrivileges` blockierte sudo | sudo-Gate lief zu früh | FIX-2: `type=data/local` ohne pauschales sudo-Gate |
| `type=data` enthielt `/opt` und `/opt/containerd` | zu breiter Data-Scope | FIX-3/FIX-4: explizite Source-Planung, kein `/opt` |
| `/home/volker` im Dienstkontext nicht lesbar | `ProtectHome=yes` schirmt Home ab | FIX-5/FIX-6: explizite Testdatenquelle `/mnt/setuphelfer/test-data` |
| autofs/systemd-automount führte zu STORAGE-PROTECTION-004 | Safe-Device sah `systemd-1` statt echtes Blockgerät | FIX-7/FIX-8: robuste Auflösung auf `/dev/sda4`, Vereinheitlichung mit `storage_detection` |
| Verschlüsselung wurde zunächst ignoriert | Payload nicht sauber normalisiert | Encryption-Payload fix, harter Fehler statt Warnung |
| Restore-Path-Prüfung hatte `lstrip("./")`-Problem | Pfad-Traversal konnte falsch normalisiert werden | echte Pfadvalidierung und Blockade gefährlicher Einträge |

---

## 4. Erfolgreiche Teststände

### HW1-01 – Unverschlüsseltes Data-Backup

Status: **bestanden**

Geprüft:

- stabile Mount-Basis
- `type=data/local`
- explizite Datenquelle `/mnt/setuphelfer/test-data`
- Backup erfolgreich
- Verify deep erfolgreich
- Restore Preview erfolgreich
- keine sudo-Nutzung
- keine falschen Quellen
- keine Permission-/Storage-Protection-Fehler

### HW1-02 – Verschlüsseltes Data-Backup

Status: **bestanden**

Geprüft:

- verschlüsseltes Backup erfolgreich
- Verify deep mit richtigem Passwort erfolgreich
- Restore Preview mit richtigem Passwort erfolgreich
- Negativtest mit falschem Passwort erfolgreich
- deterministische Fehlercodes:
  - `backup.verify_decrypt_failed`
  - `backup.restore_decrypt_failed`
- kein stiller Erfolg
- kein 500er-Crash

### HW1-03 – Kontrollierte Negativtests

Status: **bestanden**

Geprüfte Negativfälle:

| Test | Erwartung | Ergebnis |
|---|---|---|
| Manifest entfernt | `backup.failed_manifest_missing` | bestanden |
| Datei manipuliert | `backup.verify_integrity_failed` | bestanden |
| Archiv beschädigt | `backup.verify_archive_unreadable` | bestanden |
| Ziel unter `/media/volker` | STORAGE-PROTECTION | bestanden |
| nicht beschreibbarer Zielpfad | PERM-GROUP / not writable | bestanden |
| Pfad-Traversal im Restore | Restore blockiert Einträge | bestanden |

---

## 5. Diagnose- und Fehlercodes aus HW1

Wichtige genutzte Diagnose-IDs:

- `BACKUP-MANIFEST-001`
- `BACKUP-ARCHIVE-002`
- `BACKUP-HASH-003`
- `BACKUP-SOURCE-PERM-032`
- `STORAGE-PROTECTION-004`
- `STORAGE-PROTECTION-005`
- `PERM-GROUP-008`
- `OWNER-MODE-023`
- `RESTORE-PATH-004`
- `SYSTEMD-NNP-031`
- `SERVICE-CONFLICT-033`
- `SERVICE-CONFLICT-034`
- `SERVICE-CONFLICT-035`
- `SERVICE-CONFLICT-036`

Wichtige API-Codes:

- `backup.success`
- `backup.verify_success`
- `backup.restore_preview_ok`
- `backup.failed_manifest_missing`
- `backup.verify_integrity_failed`
- `backup.verify_archive_unreadable`
- `backup.path_invalid`
- `backup.backup_target_not_writable`
- `backup.restore_blocked_entries`
- `backup.source_permission_denied`
- `backup.sudo_blocked_by_nnp`
- `backup.verify_decrypt_failed`
- `backup.restore_decrypt_failed`

---

## 6. Wissensdatenbank und Dokumentation

Synchronisierte Bereiche:

- `docs/developer/BACKUP_RECOVERY_ENGINES.md`
- `docs/developer/TODO_REAL_DATA_HOME_BACKUP.md`
- `docs/knowledge-base/diagnostics/DIAGNOSIS_CATALOG.md`
- `docs/knowledge-base/diagnostics/STORAGE_PROTECTION.md`
- `docs/knowledge-base/diagnostics/SERVICE_CONFLICTS.md`
- `docs/knowledge-base/test-evidence/HW_EXEC_1_EXTERNAL_NVME_REPORT.md`
- `docs/faq/RESCUE_FAQ.md`
- `docs/faq/STORAGE_PROTECTION_FAQ.md`
- `docs/faq/SERVICE_CONFLICT_FAQ.md`
- `frontend/src/locales/de.json`
- `frontend/src/locales/en.json`

Die Wissensbasis wurde für den Umfang HW1-01 bis HW1-03 synchronisiert. Eine vollständige Aussage über jede Diagnose und jede Randzeile im gesamten Repo wird damit nicht behauptet.

---

## 7. Bewusst offene Themen

Diese Themen sind geplant, aber bewusst nicht Teil der bisherigen HW1-Erfolgsdefinition:

- echte `/home`-Daten
- Full-System-Backup
- Container-/Runtime-Daten
- LVM / komplexe Storage-Topologien
- größere Datenmengen und Performance
- Bootfähigkeit nach echtem Restore
- Raspberry-Pi-spezifische Restore-Tests

### TODO: echte `/home`-Daten

Separat dokumentiert in:

`docs/developer/TODO_REAL_DATA_HOME_BACKUP.md`

Regeln:

- kein automatisches `/home/*`-Scanning
- keine fremden Home-Verzeichnisse
- keine root-only-Umgehung im Standard-`type=data`
- nur explizite Pfade
- Datenschutz-/Rechteprüfung
- Diagnose bei Permission-Problemen

---

## 8. Aktueller Stand

```text
HW1-01: success
HW1-02: success
HW1-03: success
HW1-04: success
HW1-05: success
HW1-06: success (R2 nach FIX-12, EVID-2026-HW1-06-R2)
HW1-07: success (Reproduzierbarkeit bestätigt, EVID-2026-HW1-07)
Nächster sinnvoller Schritt: HW1-Folgetests auf derselben stabilen NVMe-Basis fortführen
```

## 9. HW1-05 (erledigt, 2026-04-27)

Ausgeführt: Restore-Verhalten ohne produktiven Root-Restore analysiert (Preview-Baseline, Inhaltsanalyse, erweiterte Zielvalidierung A-D, simulierte Restore-Risiken), Evidence `EVID-2026-HW1-05`, Matrix/Report aktualisiert. PrivateTmp-Verhalten wurde explizit bestätigt (kein Bug, Service-Isolation).

## 10. Empfehlung für HW1-06

Vor HW1-06 sollte FIX-9 (API-Konsistenz) auf dem Zielhost gegengeprüft werden: harmonisierte List-Validierung, sichtbare `selected_sources` in `backup/create`, und PrivateTmp-Hinweise im Preview-Response. Danach kann HW1-06 ohne Pi/USB/SD und weiterhin ohne produktiven Root-Restore geplant werden.

## 11. HW1-06 (Retry nach NVME-Rebuild, 2026-04-28)

Ausgeführt: **teilweise** (Pre-Check, Backup, Verify, Restore-Aufrufe und Negativtests durchgeführt).

Ergebnis:

- Pre-Check auf neuer NVMe-Basis grün (`/mnt/setuphelfer/backups` ext4, korrekte Rechte, `restore-target` vorhanden).
- Baseline-Backup erfolgreich (`backup.success`) und Verify deep erfolgreich (`backup.verify_success`).
- Restore-Aufruf mit `mode=restore` + `target_dir=/mnt/setuphelfer/restore-target` antwortete dennoch mit `mode=preview` / `backup.restore_preview_ok`.
- Negativziele (`/media/...`, non-writable, `/`) wurden nicht mit den erwarteten Zielschutz-Fehlern blockiert, sondern ebenfalls als Preview erfolgreich beantwortet.

Evidence: `EVID-2026-HW1-06`.

Bewertung: **HW1-06 nicht bestanden** (Restore-Zielvalidierung im aktuellen API-Verhalten nicht belastbar nachweisbar).

## 12. HW1-06-R2 (erfolgreich, 2026-04-28)

Nach FIX-12 wurde HW1-06 vollständig erneut ausgeführt:

- Pre-Check grün (Service-Konflikte frei, Version 1.5.0.0, list stabil, Rechte auf Backup-/Restore-/Testdatenpfad korrekt)
- Baseline-Backup erfolgreich (`backup.success`) mit Quelle `/mnt/setuphelfer/test-data`
- Verify deep erfolgreich (`backup.verify_success`)
- Preview erfolgreich (`backup.restore_preview_ok`, keine blocked entries)
- Echter Restore auf `/mnt/setuphelfer/restore-target/hw1-06-r2` erfolgreich (`backup.restore_success`)
- Inhaltsvalidierung erfolgreich (README/sample/manifest vorhanden und konsistent, keine Einträge außerhalb target_dir)
- Negativtests deterministisch:
  - `/media/...` -> `backup.restore_target_invalid` + `STORAGE-PROTECTION-005`
  - non-writable -> `backup.restore_not_writable` + `PERM-GROUP-008`
  - `/` -> `backup.restore_target_invalid` + `RESTORE-RUNTIME-006`

Evidence: `EVID-2026-HW1-06-R2`.

Bewertung: **HW1-06 bestanden**.

## 13. HW1-07 (Reproduzierbarkeit, 2026-04-28)

HW1-07 bestätigte die erfolgreiche Kette aus HW1-06 erneut ohne zusätzliche Code-Fixes:

- Backup (`type=data`) erfolgreich mit Quelle `/mnt/setuphelfer/test-data`
- Verify deep erfolgreich
- Preview erfolgreich ohne `blocked_entries`
- Echter Restore erfolgreich in dediziertes Ziel `/mnt/setuphelfer/restore-target/hw1-07`
- Inhaltsvalidierung vollständig (README/sample/MANIFEST konsistent, keine Einträge außerhalb `target_dir`)

Evidence: `EVID-2026-HW1-07`.

Bewertung: **Reproduzierbarkeit der NVMe-Recovery-Kette bestätigt**.

### Kernerkenntnis HW1-06/HW1-07 (final)

- **HW1-06 (Controlled Restore):**
  - Ursache der Vorfehler: Restore lief historisch effektiv als Preview.
  - Fix: **FIX-12 Restore-Enforcement** (strikte Trennung `preview` vs. `restore`, `target_dir` Pflicht, deterministische Zielschutz-Fehler).
  - Ergebnis: echter Restore auf kontrollierten Zielpfad reproduzierbar möglich.
  - Rest-Risiken: falscher Zielpfad, fehlende Schreibrechte, Root-/Media-Ziele.

- **HW1-07 (Reproduzierbarkeit):**
  - identischer Ablauf wie HW1-06 erneut erfolgreich.
  - keine funktionalen Abweichungen.
  - bestätigt: stabile Pipeline und deterministische Ergebnisse auf der NVMe-Basis.
