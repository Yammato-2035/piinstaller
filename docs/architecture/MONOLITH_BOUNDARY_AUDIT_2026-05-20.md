# Monolith Boundary Audit — vor Rettungsstick-Ausbau

**Datum:** 2026-05-20  
**HEAD (vor Audit-Artefakten):** `2a4ed5e` — *Pivot BR-001 release gate to offline rescue stick.*  
**Runtime-Gate:** `./scripts/check-runtime-deploy-gate.sh` → **Exit 0** (Analyse erlaubt; kein produktiver Backup-/Restore-Lauf in diesem Audit)  
**Dienste:** `setuphelfer.service` **active**, `setuphelfer-backend.service` **active**  
**Fremde uncommitted Änderungen:** ja (u. a. Lab-Acceptance, Packaging, Frontend — **nicht** Teil dieses Commits)

**Regeln dieses Audits:** kein Backup, Restore, Verify Deep, apt, Unfreeze, kein großer Refactor.

---

## 1. Größte Monolith-Dateien (ohne venv)

| Größe | Datei | Rolle / Risiko |
|------:|-------|----------------|
| ~738 KiB | `backend/app.py` | **~100 HTTP-Routen**, Backup/Restore/USB/Mount/Verify inline — höchstes Wartungsrisiko |
| ~201 KiB | `backend/deploy/routes.py` | Deploy/Rescue-Runner-HTTP-Oberfläche, parallel zu `app.py` |
| ~82 KiB | `backend/modules/control_center.py` | Pi-Desktop-Features (nicht Rescue-Kern) |
| ~57 KiB | `backend/tools/backup_runner.py` | **Kanonischer** systemd-Backup-Lauf (tar/pigz, finalize, SHA256, Verify Deep) |
| ~35 KiB | `backend/core/safe_device.py` | Mount-Quelle, STORAGE-PROTECTION, `validate_write_target` |
| ~37 KiB | `backend/core/dev_dashboard.py` | Cockpit-Aggregation |
| ~28 KiB | `backend/core/dev_dashboard_cockpit.py` | Gates, BR-001-Split |
| ~23 KiB | `backend/modules/backup.py` / `backup_engine.py` / `backup_verify.py` | Manifest, Archiv-Erstellung, Verify Basic/Deep |
| ~22 KiB | `backend/preflight/backup.py` | Preflight-Plan-Store (Rescue-Orchestrator importiert) |
| ~22 KiB | `backend/safety/write_guard.py` | Inspect-basierte Write-Safety |
| ~114 Dateien | `backend/deploy/runner_rescue_*.py` (+ weitere Runner) | Vorbereitung/Evidence — **Gefahr: Logik-Duplikate** wenn Rescue-Features dort statt in Core landen |

---

## 2. Verantwortlichkeiten (Ist)

| Bereich | Primäre Anker | Anmerkung |
|---------|---------------|-----------|
| HTTP/API | `app.py`, `api/routes/*`, `deploy/routes.py`, `rescue/routes.py` | Vier Router-Ebenen |
| Storage Discovery | `modules/storage_detection.py`, `core/safe_device.py`, `app.py` (lsblk/findmnt), `deploy/runner_rescue_storage_discovery.py` | **3+ Parser-Pfade** |
| Mount | `core/backup_target_auto_prepare.py`, `core/backup_target_service_access.py`, `app.py`, `deploy/runner_rescue_readonly_mount_orchestrator.py` | Live-Mount vs. Rescue-RO getrennt, aber überlappend |
| Write Safety | `core/safe_device.py`, `safety/write_guard.py`, `deploy/real_write_guard.py`, `deploy/hardware_gate.py` | Inspect- vs. Deploy- vs. Runtime-Guards |
| Backup Profiles / Excludes | `core/backup_profiles.py`, `core/backup_archive_options.py` | Soll **eine** Exclude-Quelle für Live + Rescue |
| Backup Runner | `tools/backup_runner.py` | Subprocess/systemd — **nicht duplizieren** |
| Verify | `modules/backup_verify.py` | Von Runner + API genutzt |
| Restore Preview | `modules/rescue_restore_dryrun.py`, `rescue/orchestrator.py`, `deploy/runner_rescue_restore_preview_orchestrator.py` | Fachlogik + Deploy-Handoff |
| Backup Discovery (Rescue) | `modules/rescue_backup_discovery.py`, `deploy/runner_rescue_backup_discovery_verify.py` | Modul vs. Runner-JSON |
| Evidence | `tools/backup_evidence_collector.py`, `core/dev_dashboard*.py`, `deploy/runner_*_handoff` | Viele Handoff-Pfade |
| Notifications | `core/notification_service.py`, `core/notification_settings.py` | Runner + API |
| Live Preflight | `core/package_activity.py`, `preflight/backup.py`, `core/service_conflict_guard.py` | Live-spezifisch |
| Rescue API | `rescue/orchestrator.py`, `rescue/routes.py` | Nutzt Core-Module (gut), lädt Module per `importlib` (fragil) |

---

## 3. Erkannte Duplikate / Konflikte (Matrix)

| Bereich | Vorhandene Dateien | Doppelte Funktion | Zielmodul (Soll) | Aktion |
|---------|-------------------|-------------------|------------------|--------|
| **1. Storage Discovery** | `storage_detection.py`, `safe_device.py`, `app.py`, `runner_rescue_storage_discovery.py`, `inspect_storage.py` | lsblk/blkid/findmnt mehrfach; Rescue-Runner schreibt eigene Handoffs | `core/storage/discovery.py` | **Extract** Parser; Rescue-Runner nur Handoff + Core-Aufruf |
| **2. Mount Logic** | `backup_target_auto_prepare.py`, `backup_target_service_access.py`, `app.py` USB-Mount, `runner_rescue_readonly_mount_orchestrator.py` | Mount-Flatten, target-check, RO-Plan | `core/mount/` + `rescue/rescue_readonly_source.py` | **Freeze** API; Rescue nur RO-Orchestrierung |
| **3. Backup Profiles** | `backup_profiles.py`, `backup_archive_options.py`, Profile in `app.py` create | full-expert / full-root-stable / später offline-full | `core/backup/profiles.py` | **Ein** Profil-Builder; `rescue/offline-full` = Profil-ID |
| **4. Backup Runner** | `backup_runner.py` (tools), Logik-Split in `app.py` create | Nur ein Runner für tar-Archiv | `tools/backup_runner.py` bleibt | **Kein** zweiter Runner; Rescue ruft gleichen Entry mit `SOURCE_ROOT` |
| **5. Verify** | `backup_verify.py`, `_runner_verify_deep` in Runner, API in `app.py` | verify_basic/deep zentral OK | `core/verify/` (Wrapper um Modul) | **Import** stabilisieren, keine Rescue-Kopie |
| **6. Restore Preview** | `rescue_restore_dryrun.py`, `rescue/orchestrator.py`, Deploy-Preview-Runner | Dry-run Pipeline doppelt exponiert | `core/restore/preview.py` + `rescue/rescue_restore_preview.py` | Runner = Thin-Handoff |
| **7. Evidence** | `backup_evidence_collector.py`, release-gates JSON, deploy handoffs | JSON-Schemas teils parallel | `core/evidence/writer.py` | **Ein** Writer-Contract |
| **8. Notifications** | `notification_service.py`, `notification_settings.py` | Config-Laden im Runner und API | `core/notifications/` | Bereits nah am Ziel — nur Pfade dokumentieren |
| **9. Safety** | `safe_device.py`, `write_guard.py`, `real_write_guard.py`, `hardware_gate.py` | Zielprüfung vs. Inspect-Safety vs. Deploy | `core/safety/` | **Klar:** Runtime=`safe_device`; Rescue-Preview=`write_guard`+Inspect; Deploy=`real_write_guard` |
| **10. Live Preflight** | `package_activity.py`, `preflight/backup.py` | Paket-Konflikt Live vs. Rescue-Plan-Store | `live/package_activity.py` | Rescue **ohne** apt-Timer-Logik |
| **11. HTTP Monolith** | `app.py` | Fachlogik in Route-Handlern | Adapter nur | **Langfristig** Routes → Services; **nicht** vor Stick-Build |

---

## 4. Risiko pro Bereich

| Risiko | Schwere | Begründung |
|--------|---------|------------|
| Neuer Rescue-Code kopiert lsblk/findmnt | **KRITISCH** | BR-001-OFFLINE würde von abweichender Medienklassifikation scheitern |
| Zweiter Backup-Runner auf Stick | **KRITISCH** | Doppelte partial/finalize/SHA256-Semantik |
| `app.py` weiter wachsen | **HOCH** | Jede Stick-API landet sonst im Monolithen |
| 114+ Deploy-Runner ohne Core-Abhängigkeit | **MITTEL** | Vorbereitung OK, aber „falsche“ Implementierung in Runnern |
| `importlib` in `rescue/orchestrator.py` | **MITTEL** | Schwer testbar, bricht bei Verschiebungen |
| `write_guard` vs. `safe_device` Verwechslung | **HOCH** | Operator könnte falsche Guard-Lesart nutzen |

---

## 5. Empfohlene Zielmodule (Kurz)

Siehe verbindlich: [`MODULE_BOUNDARIES_TARGET_2026-05-20.md`](MODULE_BOUNDARIES_TARGET_2026-05-20.md)  
Migrationsreihenfolge: [`MONOLITH_DECOMPOSITION_PLAN_2026-05-20.md`](MONOLITH_DECOMPOSITION_PLAN_2026-05-20.md)  
Anti-Duplikat: [`NO_DUPLICATE_MODULE_RULES.md`](NO_DUPLICATE_MODULE_RULES.md)  
Rettungsstick: [`../rescue-stick/RESCUE_STICK_CORE_DEPENDENCIES_2026-05-20.md`](../rescue-stick/RESCUE_STICK_CORE_DEPENDENCIES_2026-05-20.md)

---

## 6. Abnahme-Kriterium Rettungsstick

Rettungsstick-Ausbau **nur**, wenn:

1. Storage/Mount/Safety/Backup/Verify über **Core** (oder dokumentierte Adapter) laufen.  
2. Neue Dateien unter `backend/rescue/` sind **Orchestrierung**, keine zweiten Parser/Runner.  
3. Abweichungen haben **ADR** in `docs/architecture/adr/`.
