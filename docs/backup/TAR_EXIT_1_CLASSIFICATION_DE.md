# GNU tar Exitcode 1 – Klassifikation (Setuphelfer)

**Stand:** 2026-05-17 · **Evidence:** `docs/evidence/runtime-results/br001_tar_exit1_forensics_2026-05-16.json` (Job `927469d42503`)

## Hintergrund

GNU **tar** beendet sich mit Exitcode **1**, wenn während des Laufs **Warnungen** auftraten (z. B. geänderte Live-Dateien, ignorierte Sockets), auch wenn der Stream bis zum Ende geschrieben wurde. Das bedeutet **nicht automatisch**, dass das Archiv unbrauchbar ist — aber auch **nicht automatisch**, dass Setuphelfer den Lauf als Erfolg werten darf.

Der isolierte Runner (`backend/tools/backup_runner.py`) behandelt heute **jeden** `returncode != 0` nach dem Tar-Pipeline-Lauf als **`abort_reason: tar_failed`**, löscht die `.partial` und erzeugt **kein** finales `.tar.gz` (kein SHA256, kein Verify Deep).

## Klassifikationsstufen (Entwurf)

| ID | Bedeutung |
|----|-----------|
| `TAR_OK` | Exit 0, keine fatalen Meldungen |
| `TAR_LIVE_FILE_CHANGED_ONLY` | Exit 1, nur „file changed“ auf **volatile** Pfaden |
| `TAR_SOCKET_IGNORED_ONLY` | Exit 1, nur „Socket ignoriert“ auf **volatile** Pfaden |
| `TAR_VOLATILE_WARNINGS_ONLY` | Exit 1, Mischung erlaubter volatile Warnungen |
| `TAR_CRITICAL_WARNING` | z. B. Dateiänderung unter `/etc`, `/boot` |
| `TAR_IO_ERROR` | Input/output error, short-write auf Zielstream |
| `TAR_PERMISSION_CRITICAL` | Permission denied auf kritischem Pfad |
| `TAR_FATAL` | Unerwartete Meldungen, EOF, kein Speicher, sonst Exit 1 |

Implementierung: `backend/core/backup_tar_warning_classification.py` — im isolierten Runner (`backend/tools/backup_runner.py`) seit 2026-05-17 integriert (Workspace; Deploy separat).

## Harte Regeln (Safety)

Tar Exit **1** darf **nur** nach erfolgreicher Nachprüfung von einem harten Fehler herabgestuft werden, wenn **alle** zutreffen:

1. Keine I/O-Fehler, kein „No space left“, kein „Unexpected EOF“
2. Keine kritischen Systempfade in Warnungen (`/etc`, `/boot`, `/usr`, …)
3. Nur erlaubte volatile Muster (siehe Knowledge Base)
4. **Finales** `.tar.gz` existiert (Rename von `.partial`)
5. **SHA256** des Archiv-Payloads erfolgreich
6. **Verify Deep** erfolgreich

Ohne finales Archiv: Status bleibt **`failed`** / **`blocked`**, nie **`success`**.

## BR-001-Lauf 927469d42503 (Kurz)

- Profil **`full-expert`**, ~**227 GiB** in `.partial`, dann Exit **1**
- Stderr: gpg-agent-Sockets, Docker-Desktop-Sockets, viele ibus-Cache-Sockets, **eine** Journal-Dateiänderung
- **Keine** I/O-/Space-/EOF-/kritischen Permission-Meldungen
- Klassifikation der Warnungen: **`TAR_VOLATILE_WARNINGS_ONLY`**
- Betriebsergebnis: **`failed`** (Partial gelöscht, kein Archiv)

## Stabiles Tar-Profil (Vorschlag)

### Zusätzliche Excludes (full-expert / BR-001)

Bereits bei `recommended` / `fast-system`: `/var/cache`, `/var/tmp`.

Für volatile Live-Daten zusätzlich prüfen:

| Muster | Begründung |
|--------|------------|
| `/var/log/journal` | systemd-Journal wächst/rotiert während des Laufs |
| `/home/*/.cache` | Browser, ibus, Desktop-Caches |
| `/home/*/.local/share/Trash` | Papierkorb |
| Browser-Profile-Caches | z. B. unter `.var/app/.../cache` |

**Docker Desktop** (`~/.docker/desktop/*.sock`, VM-Sockets): **nicht** pauschal aus dem Root-Backup entfernen ohne Strategie — Optionen: Docker separat sichern, Dienste stoppen/Snapshot, oder als **nicht-deterministischen** Live-Bereich dokumentieren und von Verify Deep abhängig machen.

### Option `--warning=no-file-changed`

| Aspekt | Bewertung |
|--------|-----------|
| Vorteil | Weniger Exit-1 durch Journal/Logs; stabilerer Exitcode |
| Risiko | Verdeckt echte Änderungen auf **nicht-volatile** Pfaden; tar meldet dann nicht mehr „file changed“ |
| Exitcode | Stabilisiert nur **Dateiänderungs**-Warnungen, **nicht** Sockets oder I/O |
| Verify Deep | **Bleibt zwingend** — weniger stderr heißt nicht integreres Archiv |

### Nicht verwenden: `--ignore-failed-read`

Liest fehlgeschlagene Dateien **still** überspringend. Das würde Safety-Gates untergraben (fehlende kritische Dateien ohne harten Abbruch). Setuphelfer lehnt diese Option ab.

## Runner-Integration (Workspace)

Nach `tar`-Pipeline (`subprocess_returncode != 0`):

1. Vollständiges stderr klassifizieren; Felder in `status.json`: `tar_warning_classification`, `tar_warning_downgrade_allowed`, `operational_success_allowed`, `final_archive_required`, `sha256_required`, `verify_deep_required`, `volatile_warning_paths`, `fatal_patterns_found`, `tar_downgrade_blockers`.
2. **Volatile-only** + lesbare `.partial` → Finalisierung (SHA256, Manifest, Rename) und **Verify Deep** im Runner.
3. Nur bei `backup.success_with_warnings` + `warning_status: completed_with_warnings` + `backup_integrity_status: verified` (nach SHA256 **und** Verify Deep).
4. **Kein** finales Archiv → `backup.warning_not_promoted` / `tar_volatile_warning_without_final_archive`, Partial-Cleanup wie bisher.
5. I/O, Space, EOF, kritische Pfade → weiterhin hart `backup.failed` / `tar_failed`.

**Kein pauschaler Erfolg bei Exit 1.** BR-001 bleibt ohne Integritätskette rot.

## Nächste Schritte (ohne automatischen BR-001)

1. Nach **Deploy-Freigabe** Runner unter `/opt` aktualisieren und Gate erneut prüfen.
2. Profilwahl für Alltag: `recommended` statt `full-expert`, wenn kein echtes Root-Image nötig ist.
3. Excludes/Evidence für Docker und Journal dokumentiert halten.

## Verweise

- FAQ: `docs/faq/BACKUP_RESTORE_FAQ_DE.md` (Abschnitt tar Exit 1)
- KB: `docs/knowledge-base/backup/TAR_EXIT_1_LIVE_FILES.md`
- Tests: `backend/tests/test_backup_tar_warning_classification_v1.py`
