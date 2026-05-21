# Core Storage & Mount Facades

**Stand:** 2026-05-20  
**Phase:** B.1 / B.2 (Monolith Decomposition Plan)

---

## Zweck

Zwei kleine **Core-Facades** bündeln bestehende read-only Logik, damit Rescue- und Deploy-Runner **orchestrieren** statt Parser zu kopieren.

| Modul | Verantwortung |
|-------|----------------|
| `core.storage_facade` | lsblk/blkid Inventar, Klassifikation, Backup-/Restore-Kandidaten |
| `core.mount_facade` | findmnt Inventar, Mount-Safety, RO-Mount-**Plan** (keine Ausführung) |

---

## Rescue orchestriert nur

- `deploy/runner_rescue_storage_discovery.py` → `build_storage_inventory_snapshot`
- `deploy/runner_rescue_readonly_mount_orchestrator.py` → `plan_readonly_source_mount`

Kein eigener lsblk/findmnt-Parser mehr in diesen Runnern.

---

## Editionen

| Edition | Nutzung |
|---------|---------|
| **Core** | Facades + `storage_detection` + `safe_device` |
| **Live** | Facades mit `mode="live"`; Paketaktivität bleibt in `core.package_activity` |
| **Rescue** | Facades + Handoff JSON; RO-Mount nur Plan |
| **Cloudserver** | später dieselben Facades + Snapshot-Provider |

---

## Was Rescue nicht mehr selbst implementieren darf

- lsblk/blkid Parsing
- Backup-Target-Heuristiken
- findmnt-Flatten
- tar/backup_runner, verify_deep

---

## Legacy-Duplikate (verbleibend)

- `backend/app.py` — `_findmnt_mounts`, USB-Routen (Migration offen)
- `backend/core/safe_device.py` — umfangreiche Mount-Auflösung (Ziel: `core/mount/`)
- `backend/deploy/real_write_guard.py` — Deploy-Schreibpfad

---

## Nächste erlaubte Extraktionsschritte

1. `app.py` target-check → `mount_facade` / `safe_device` Adapter  
2. Profil `offline-full` in `backup_profiles` (kein neuer Runner)  
3. Rescue Phase C: `rescue_backup_orchestrator` ruft `backup_runner` mit `SOURCE_ROOT`

**Nicht behaupten:** Rettungsstick oder BR-001-OFFLINE sind fertig.
