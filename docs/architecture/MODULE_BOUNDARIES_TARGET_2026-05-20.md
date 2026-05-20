# Zielmodul-Grenzen — Core / Live / Rescue / Cloudserver

**Stand:** 2026-05-20  
**Status:** Verbindlich für neue Entwicklung ab BR-001-OFFLINE-Pivot.  
**Kein Big-Bang-Refactor** — siehe [`MONOLITH_DECOMPOSITION_PLAN_2026-05-20.md`](MONOLITH_DECOMPOSITION_PLAN_2026-05-20.md).

---

## Prinzipien

1. **`core/`** — wiederverwendbare Fachlogik, **keine** UI-, **keine** Boot-Kontext-Spezialfälle.  
2. **`live/`** — Desktop läuft: apt, Paketmanager, Live-tar-Risiken, experimentelle Backups.  
3. **`rescue/`** — Rettungsstick: Boot-Kontext, read-only Quelle, Offline-Orchestrierung, **keine** Core-Kopien.  
4. **`cloudserver/`** — vorbereitet, **nicht implementieren** in dieser Phase.  
5. **`app.py` / `deploy/routes.py`** — nur Routing, DTO, Auth, Fehler-Mapping.

---

## Zielbaum (Soll)

```
backend/
  core/
    storage/          # lsblk, blkid, classify removable/internal
    mount/            # findmnt flatten, mount source resolution
    safety/           # validate_write_target, system disk protection
    backup/           # profiles, archive_options, progress, telemetry
    verify/           # verify_basic, verify_deep (facade → modules/backup_verify)
    restore/          # preview planning, dry-run engines (shared)
    evidence/         # job evidence, release-gate writers
    notifications/    # effective config, mail templates
  live/
    package_activity.py
    live_preflight.py
    live_backup_orchestrator.py   # optional: thin wrapper um POST create policies
  rescue/
    rescue_boot_context.py
    rescue_storage_orchestrator.py  # mode=rescue, calls core.storage
    rescue_readonly_source.py       # RO mount plan + validation handoff
    rescue_backup_orchestrator.py   # offline-full job spawn → tools/backup_runner
    rescue_restore_preview.py       # preview API surface
  cloudserver/
    snapshot_provider.py            # stub / interface only
    incremental_backup.py
    database_hooks.py
  tools/
    backup_runner.py                # bleibt; einziger tar-Subprocess-Runner
  app.py                            # Adapter → core + live + rescue routers
```

---

## Mapping Ist → Soll (Auszug)

| Ist (heute) | Soll-Pfad | Edition |
|-------------|-----------|---------|
| `modules/storage_detection.py` | `core/storage/discovery.py` | Core |
| `core/safe_device.py` | `core/safety/target_validation.py` | Core |
| `safety/write_guard.py` | `core/safety/inspect_write_guard.py` | Core (Inspect-Daten) |
| `core/backup_profiles.py` | `core/backup/profiles.py` | Core |
| `core/backup_archive_options.py` | `core/backup/archive_options.py` | Core |
| `modules/backup_verify.py` | `core/verify/engine.py` (Re-export) | Core |
| `modules/rescue_restore_dryrun.py` | `core/restore/dryrun.py` + `rescue/rescue_restore_preview.py` | Core + Rescue |
| `core/package_activity.py` | `live/package_activity.py` | Live |
| `preflight/backup.py` | `live/live_preflight.py` (Live) / Rescue nutzt nur core.restore preview | Live |
| `deploy/runner_rescue_storage_discovery.py` | Handoff only → `rescue/rescue_storage_orchestrator.py` | Rescue |
| `deploy/runner_rescue_readonly_mount_orchestrator.py` | → `rescue/rescue_readonly_source.py` | Rescue |
| `tools/backup_runner.py` | unverändert; Rescue setzt Env `SETUPHELFER_BACKUP_SOURCE_ROOT` | Core tool |

---

## Edition-Regeln

| Edition | Backup-Gate | Module |
|---------|-------------|--------|
| **Desktop Privat (Release)** | BR-001-OFFLINE | `rescue/*` + `core/*` |
| **Desktop Live** | experimentell | `live/*` + `core/*` (Profile system-stable) |
| **Cloudserver** | Snapshot + inkrementell | `cloudserver/*` (später) + `core/*` |

---

## Verboten

- Neue `lsblk`/`findmnt`-Parser unter `deploy/runner_rescue_*` mit Persistenzlogik.  
- Zweiter tar-Runner unter `rescue/` oder `deploy/`.  
- Verify-Deep-Implementierung außerhalb `modules/backup_verify.py` / `core/verify/`.  
- Eigene Write-Guard-Regeln nur für Rescue ohne ADR.

---

## `app.py`-Regel

Neue Endpoints:

1. Service-Funktion in `core/` oder `rescue/`.  
2. Route in `rescue/routes.py` oder schlankem Router — **nicht** 200 Zeilen Logik in `app.py`.

Bestehende Monolith-Routen: **nicht anfassen** in Phase A–B außer Extraktion mit pytest-Sicherheitsnetz.
