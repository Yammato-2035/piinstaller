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

**Exit A:** Rettungsstick-Team weiß, welche Funktionen **importiert** werden dürfen.

---

## Phase B — Extract Small Core (kleine Moves, je 1 PR)

| Schritt | Extract | Von → Nach | Risiko | Tests |
|---------|---------|------------|--------|-------|
| B.1 Storage parser facade | `core/storage/__init__.py` re-export `detect_block_devices` | `storage_detection.py` | Mittel | `test_storage_detection_*`, `test_safe_device_*` |
| B.2 Target check facade | `core/mount/target_inspect.py` | `backup_target_service_access` + `safe_device.resolve_mount_source` | Mittel | `test_backup_target_*` |
| B.3 Profile builder single entry | `core/backup/build_create_job.py` | `app.py` create-Body + profiles | Hoch | `test_backup_profiles_v1`, `test_backup_create_*` |
| B.4 Evidence writer wrapper | `core/evidence/job_end.py` | `backup_evidence_collector.py` | Niedrig | `test_backup_evidence_collector_v1` |
| B.5 Notification config | `core/notifications/effective.py` | `notification_settings` | Niedrig | notification tests |

**Rollback je Schritt:** Re-export aus altem Modul, keine Löschung bis grün.

**Nicht anfassen:** `deploy/runner_*` Massenverschiebung, `app.py` USB-Routen-Komplettumbau.

---

## Phase C — Rescue Orchestrator (nach B.1–B.2)

| Schritt | Inhalt | Nutzt Core | Tests |
|---------|--------|------------|-------|
| C.1 `rescue_boot_context.py` | `mode=rescue`, paths, readonly default | install_paths | Unit |
| C.2 `rescue_storage_orchestrator.py` | Ersetzt Logik-Duplikat in `runner_rescue_storage_discovery` | `core/storage` | `test_deploy_runner_rescue_storage_discovery_v1` (Handoff gleich) |
| C.3 `rescue_readonly_source.py` | RO-Mount-Plan | `core/mount` | `test_deploy_runner_rescue_readonly_mount_orchestrator_v1` |
| C.4 `rescue_backup_orchestrator.py` | Job-Env + systemd spawn | `tools/backup_runner`, profiles `offline-full` | HW später |
| C.5 Deploy-Runner dünn | Runner nur `write_json_handoff` | — | bestehende Deploy-Tests |

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
