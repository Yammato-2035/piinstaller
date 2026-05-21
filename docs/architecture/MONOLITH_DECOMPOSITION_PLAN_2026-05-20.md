# Monolith Decomposition Plan — risikoarm, ohne großen Refactor

**Stand:** 2026-05-20  
**Voraussetzung:** [`MONOLITH_BOUNDARY_AUDIT_2026-05-20.md`](MONOLITH_BOUNDARY_AUDIT_2026-05-20.md)

---

## Phase A — Freeze Interfaces (sofort, vor Stick-Build)

| Schritt | Dateien | Risiko | Tests | Rollback | Nicht anfassen |
|---------|---------|--------|-------|----------|----------------|
| A.1 Public API dokumentieren | `backup_profiles.py`, `backup_verify.py`, `safe_device.py`, `backup_runner.py` | Niedrig | Bestehende pytest | — | `app.py` Body |
| A.2 Rescue-Orchestrator-Imports festhalten | `rescue/orchestrator.py` | Niedrig | `test_rescue_orchestrator_*` | Revert Import-Pfad | Execute-Restore |
| A.3 Profil-ID `offline-full` reservieren | `backup_profiles.py` (nur Konstante/Doku) | Niedrig | `test_backup_profiles_v1` | Git revert | Runner-Verhalten |
| A.4 `NO_DUPLICATE_MODULE_RULES` + `check-module-boundaries.sh` | docs + scripts | Niedrig | `test_module_boundaries_v1` | Script löschen | — |
| A.5 **Module Freeze Register** | `MODULE_FREEZE_REGISTER_2026-05-20.md` | Niedrig | — | — | — |

**Exit A:** erfüllt (2026-05-20).

---

## Phase B — Extract Small Core (kleine Moves, je 1 PR)

| Schritt | Extract | Von → Nach | Risiko | Tests | Status |
|---------|---------|------------|--------|-------|--------|
| B.1 Storage facade | `core/storage_facade.py` | `storage_detection` + rescue flat lsblk | Mittel | `test_core_storage_facade_v1` | **Done 2026-05-20** |
| B.2 Mount facade | `core/mount_facade.py` | findmnt plan/inventory | Mittel | `test_core_mount_facade_v1` | **Done 2026-05-20** |
| B.2b Runner migration | rescue storage + readonly mount runners | Facades | Mittel | deploy runner tests | **Done 2026-05-20** |
| B.3 Target check facade | `core/mount/target_inspect.py` | `backup_target_service_access` + `safe_device` | Mittel | `test_backup_target_*` | Offen |
| B.3 Profile builder single entry | `core/backup/build_create_job.py` | `app.py` create-Body + profiles | Hoch | `test_backup_profiles_v1`, `test_backup_create_*` |
| B.4 Evidence writer wrapper | `core/evidence/job_end.py` | `backup_evidence_collector.py` | Niedrig | `test_backup_evidence_collector_v1` |
| B.5 Notification config | `core/notifications/effective.py` | `notification_settings` | Niedrig | notification tests |

**Rollback je Schritt:** Re-export aus altem Modul, keine Löschung bis grün.

**Nicht anfassen:** `deploy/runner_*` Massenverschiebung, `app.py` USB-Routen-Komplettumbau.

---

## Phase C — Rescue Orchestrator (nach B.1–B.2)

| Schritt | Inhalt | Nutzt Core | Tests | Status |
|---------|--------|------------|-------|--------|
| C.1 `rescue/boot_context.py` | Boot-Kontext read-only | install_paths, mount_snapshot hints | `test_rescue_boot_context_v1` | **done** |
| C.2 `rescue/backup_orchestrator.py` | Offline-Backup-**Plan** only | `backup_profiles`, boot_context | `test_rescue_offline_backup_plan_v1` | **done** |
| C.3 `offline-full` Profil | Metadaten, Excludes | `get_backup_profile` | `test_backup_profiles_offline_full_v1` | **done** |
| C.4 Restore-Preview-Handoff | `restore_preview_orchestrator`, `restore_profiles`, `backup_before_write_gate` | `rescue_restore_dryrun`, `backup_verify` (Ref only) | `test_rescue_restore_preview_plan_v1` | **done** |
| C.5 Deploy-Runner dünn | Runner nur Handoff | Facades | bestehende Deploy-Tests | teilweise (B.1/B.2) |
| C.6 Backup **execute** auf HW | systemd + `backup_runner` | Safety + target-check | HW später | **nicht** in C.1–C.3 |

**Nicht anfassen:** ISO-Build-Produktion, Partitionierungsassistent, Cloudserver.

---

## Phase D — Cloudserver (später)

- `cloudserver/snapshot_provider.py` Interface.  
- Inkrementell über bestehende `backup_engine` / zukünftige Provider.  
- **Keine** Rescue-Logik kopieren.

---

## Empfehlung: Rettungsstick jetzt oder extrahieren?

| Option | Wann |
|--------|------|
| **Minimal extrahieren zuerst (empfohlen)** | Phase **A + B.1 + B.2** (1–2 Tage), dann Stick C.1–C.3 |
| **Direkt Stick bauen** | Nur wenn jeder neue Stick-Code **explizit** Core importiert und `check-module-boundaries.sh` grün/warning-frei |

**Nicht empfohlen:** ISO/Offline-UI vor gefrorenen Storage/Mount/Safety-Interfaces.
