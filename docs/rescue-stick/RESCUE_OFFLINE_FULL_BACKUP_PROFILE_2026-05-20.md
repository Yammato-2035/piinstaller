# Offline-Full Backup-Profil (Phase C.3)

**Stand:** 2026-05-20  
**Modul:** `backend/core/backup_profiles.py` → `get_backup_profile("offline-full")`

---

## Profil-ID

`offline-full` — BR-001-OFFLINE / Rettungsstick, **nicht** identisch mit Live-`full-root-stable`.

| Eigenschaft | offline-full | full-root-stable (Live) |
|-------------|----------------|-------------------------|
| `requires_live_package_freeze` | **false** | implizit Live-Kontext |
| `requires_systemd_inhibit` | **false** | typisch Live |
| Timeshift/Chrome-Excludes | Basis-Pfade nur | erweitert (Timeshift, Caches) |
| `source_root_required` | **true** | false (läuft auf `/`) |
| Externes Ziel | **pflicht** | Policy über UI/Safety |

## Default-Excludes

`/proc`, `/sys`, `/dev`, `/tmp`, `/run`, `/mnt`, `/media`, `/run/media`

## Metadaten

- `manifest_required`, `sha256_required`: true  
- `verify_after_backup_recommended`: true  
- `write_target_must_be_external`: true  
- Nur Profil-/Optionsdaten — **kein** Tar, kein Runner-Start

## Kanonischer Runner

`backend.tools.backup_runner` (`CANONICAL_BACKUP_RUNNER_MODULE`)
