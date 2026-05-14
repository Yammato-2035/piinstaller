# Backup-Profile (Setuphelfer)

**Stand:** 2026-05-13 — **BR-019** (Gelb: Code + pytest/Vitest; HW-Abnahme Daten-Scope offen).

## Kurzüberblick

| Profil | Zweck | Runner (Stand) |
|--------|--------|------------------|
| **recommended** | Normaler Nutzerstandard: Setuphelfer-State, relevante Systemkonfiguration, ausgewählte Nutzerbereiche | **data** |
| **fast-system** | **Kein echtes „schnelles“ Backup:** aktuell derselbe **Full-Root**-Lauf wie Expertenmodus (Langläufer, hoher I/O- und Speicherbedarf). UI/API weisen per Warncodes darauf hin (`profile_fast_system_uses_full_root_v1`, `full_root_backup_long_runtime`). |
| **user-data** | Schwerpunkt Benutzerdateien unter `/home` | **data** |
| **developer** | Workspaces; standardmäßig ohne `node_modules`, `.venv`, `build`/`dist`/`target` | **data** |
| **full-expert** | Vollständiges Root-Dateisystem (bisheriger Full-Pfad) | **full** — nur mit **`confirm_full_expert`: true** |

## API (Kurz)

- **`GET`/`POST /api/backup/profiles`** — Liste mit i18n-Key-Feldern (kein Freitext).
- **`POST /api/backup/profile-preview`** — read-only Vorschau (`included_paths`, `excluded_patterns`, `warning_codes`, …), **kein** Backup-Start.
- **`POST /api/backup/create`** — `type`: `profile` | `full` | `data` | `incremental`; bei `profile` Feld **`profile`**. Legacy **`type":"full"`** bleibt gültig, mappt auf **full-expert** und setzt Warnungen; **`confirm_full_expert`** erforderlich.

## Sicherheit

- **`backup_dir`** wird nur validiert, nicht umgebogen.
- Quellen, die das Ziel einschließen würden, werden aus der logischen Preview entfernt (`excluded_source_overlaps_target:*`).
- Full-Expert behält die bekannten System-Excludes (`proc`, `sys`, …).

Siehe auch: `docs/knowledge-base/backup/BACKUP_PROFILES.md`.
