# Module Freeze Register — Storage / Mount / Safety

**Stand:** 2026-05-20  
**Zweck:** Bekannte Duplikatbereiche einfrieren; neues Wachstum nur über Core-Facades.

---

## Eingefrorene Altstellen (Legacy — nicht erweitern)

| Bereich | Datei | Status |
|---------|-------|--------|
| HTTP-Monolith Backup/USB | `backend/app.py` | Legacy — keine neue lsblk/findmnt-Logik |
| Deploy Rescue Storage (alt) | `backend/deploy/runner_rescue_storage_discovery.py` | **Migriert** auf `core.storage_facade` |
| Deploy Rescue RO Mount | `backend/deploy/runner_rescue_readonly_mount_orchestrator.py` | **Migriert** auf `core.mount_facade` |
| Storage Parser (kanonisch) | `backend/modules/storage_detection.py` | Legacy-Kern — nur via Facade erweitern |
| Mount/Safety Runtime | `backend/core/safe_device.py` | Legacy-Kern — schrittweise Facade |
| Write Guard Inspect | `backend/safety/write_guard.py` | Legacy — kein Rescue-Doppel |
| Deploy Write Guard | `backend/deploy/real_write_guard.py` | Deploy-only |
| Backup Runner | `backend/tools/backup_runner.py` | **Eingefroren** — einziger tar-Runner |
| Target Allowlist | `backend/core/backup_path_allowlist.py` | Core — nicht duplizieren |

---

## Kanonische Zielmodule (neu)

| Facade | Datei | Erlaubt |
|--------|-------|---------|
| Storage | `backend/core/storage_facade.py` | lsblk/blkid read, Kandidaten, Klassifikation |
| Mount | `backend/core/mount_facade.py` | findmnt read, RO-Plan, untracked detection |

---

## Erlaubte Änderungen

- Re-Exports und Adapter in Facades
- Runner-Orchestrierung: Handoff schreiben, Facade aufrufen
- Tests für Facades und Runner-Kompatibilität
- `check-module-boundaries.sh` Allowlist pflegen

## Verbotene Änderungen

- Neue `subprocess lsblk/findmnt` in `app.py`, `deploy/runner_*.py` (außer Allowlist-Legacy bis Migration)
- Neue `mount`/`umount` Ausführung außerhalb explizit dokumentierter Lab-Pfade
- Zweiter `backup_runner.py`
- Neue Write-Target-Validation außerhalb `safe_device` / `write_guard` / Facades

---

## Migrationsziel

Siehe `MODULE_BOUNDARIES_TARGET_2026-05-20.md` — `core/storage/`, `core/mount/` als Pakete (Facades sind Schritt B.1/B.2).

---

## Betroffene Tests

- `backend/tests/test_core_storage_facade_v1.py`
- `backend/tests/test_core_mount_facade_v1.py`
- `backend/tests/test_deploy_runner_rescue_storage_discovery_v1.py`
- `backend/tests/test_deploy_runner_rescue_readonly_mount_orchestrator_v1.py`
- `backend/tests/test_module_boundaries_v1.py`
- `backend/tests/test_safe_device_storage_protection_v1.py`
- `backend/tests/test_storage_detection_fix8_runtime_v1.py`
