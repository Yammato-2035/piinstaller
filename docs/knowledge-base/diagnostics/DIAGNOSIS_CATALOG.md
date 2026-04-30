# Diagnosis Catalog

Aktueller Starter-Katalog: **41 Diagnosefaelle** (inkl. Service-Konflikte `SERVICE-CONFLICT-033` bis `036`, siehe `SERVICE_CONFLICTS.md`).

Abgedeckte Domaenen:

- `backup_restore`
- `boot`
- `systemd_services`
- `permissions`
- `storage_filesystem`
- `network`
- `ssh_remote_access`
- `updates_packages`
- `security_hardening`
- `docker_container_runtime`
- `hardware_raspberry_pi`
- `logs_runtime`
- `app_setuphelfer_runtime`

Beispiele:

- `BACKUP-MANIFEST-001` (Manifest fehlt)
- `RESTORE-PATH-004` (Path-Containment verletzt)
- `SYSTEMD-RESTRICT-013` (Unit-Hardening blockiert Laufzeit)
- `UI-NO-BACKEND-015` (Frontend erreichbar, Backend down)
- `PERM-GROUP-008` (setuphelfer-Gruppenmodell inkonsistent; z. B. Session/Prozess nicht in `setuphelfer` trotz korrekt gesetztem Zielpfad)
- `OWNER-MODE-023` (Mountpoint-Owner/Mode unpassend; z. B. `root:root` + `755` statt `root:setuphelfer` + `0770`)
- `SYSTEMD-NNP-031` (NoNewPrivileges blockiert sudo im Restore-/Runtime-Pfad; bei falschem sudo-Gate vor Tar siehe FIX-2)
- `BACKUP-SOURCE-PERM-032` (Data-Backup enthält nicht lesbare Quellpfade; Ziel ist ok, aber Data-Scope umfasst root-only oder nicht zugreifbare Quellen, siehe FIX-3/FIX-4/FIX-5; bei Analyse immer `selected_sources` gegen erwarteten Service-Context-Scope prüfen)
- `SERVICE-CONFLICT-033` bis `036` (parallele pi-installer-/Setuphelfer-Dienste, Port-8000-Inhaber, gemischte `/opt`-Bäume; siehe `SERVICE_CONFLICTS.md`)

## HW1-03 — Beispiele, Symptome, typische Ursachen

Referenzlauf **HW1-03** (externe NVMe, produktionsnahe Pfade): Evidence z. B. `docs/knowledge-base/test-evidence/HW_EXEC_1_EXTERNAL_NVME_REPORT.md`, Matrix `hw_test_1_matrix.json` (Status success für den Lauf).

| ID | Reales Beispiel (HW1-03-Kontext) | Typische Symptome | Typische Ursachen |
|----|----------------------------------|-------------------|-------------------|
| **BACKUP-MANIFEST-001** | Verify `mode=deep` auf Archiv ohne eingebettete `MANIFEST.json` | API `backup.failed_manifest_missing`; UI „Manifest fehlt“ | Abgebrochenes Backup, manuell geändertes `.tar.gz`, altes Format ohne Manifest-Einbettung |
| **BACKUP-ARCHIVE-002** | `gzip -t` oder Tar-Lesefehler auf dem NVMe-Archiv | `backup.verify_archive_unreadable`; Diagnose im `details`-Block | Truncation, defektes Medium, Kopiervorgang unterbrochen |
| **BACKUP-HASH-003** | Deep-Verify: extrahierte Bytes ≠ Manifest-SHA | `backup.verify_integrity_failed` mit `hash_mismatch` in Details | Bit-Rot, Manipulation, falsches Archiv (gleicher Dateiname) |
| **RESTORE-PATH-004** | Preview findet `../` oder absolute Member-Pfade | `backup.restore_blocked_entries` | Bösartiges oder fehlerhaft gepacktes Archiv; historisch: unsichere Pfadnormalisierung (behoben: kein `lstrip("./")` mehr) |
| **STORAGE-PROTECTION-005** | Ziel unter `/media/…` für Schreib-Backup | `backup.path_invalid`, Reason `STORAGE-PROTECTION-005` | Automount-Pfad gewählt statt `/mnt/setuphelfer/…` |
| **PERM-GROUP-008** | Schreibprobe auf `…/backups` schlägt mit EACCES fehl trotz „richtigem“ Pfad | `backup.backup_target_not_writable` | Prozess ohne wirksame Gruppe `setuphelfer`, fehlende `SupplementaryGroups`, Owner/Mode nicht `root:setuphelfer` + `0770` |

## Restore API Enforcement (FIX-12)

- `POST /api/backup/restore` unterscheidet strikt zwischen:
  - `mode=preview` -> `backup.restore_preview_ok`
  - `mode=restore` -> `backup.restore_success` oder deterministische Ziel-/Sicherheitsfehler
- Neue/geschärfte Restore-Codes:
  - `backup.restore_target_missing` (Pflichtfeld `target_dir` fehlt)
  - `backup.restore_target_invalid` (z. B. `/`, `/media`, Storage-Protection)
  - `backup.restore_not_writable` (z. B. EACCES / `PERM-GROUP-008`)
  - `backup.restore_blocked_entries` (`RESTORE-PATH-004`)

### Diagnosefokus: `RESTORE-RUNTIME-006`

- **Beschreibung:** Restore ohne gültiges Ziel oder mit gesperrtem Zielpfad angefordert.
- **Typische Ursachen:** `target_dir` fehlt, `target_dir="/"`, kritischer Systempfad, kontraktwidriger Restore-Aufruf.
- **Empfehlung:** gültigen, beschreibbaren Zielpfad unter erlaubter Prefix-Struktur setzen (z. B. `/mnt/setuphelfer/restore-target/...`) und `mode=restore` explizit verwenden.

Kurztexte für Diagnoseausgabe:

- Beginner (DE): „Setuphelfer hat versucht, auf Daten zuzugreifen, für die er keine Berechtigung hat.“
- Expert (EN): „The data backup scope includes paths outside the service user context (e.g. /home/volker).“
