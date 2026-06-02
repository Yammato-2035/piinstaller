# Core-Facade-Freeze (Rescue-Vorbereitung)

**Stand:** 2026-06-02

## Eingefrorene Einstiegspunkte

| Facade | Datei | Nutzung |
|--------|-------|---------|
| Storage | `backend/core/storage_facade.py` | lsblk/findmnt-Kapselung |
| Mount | `backend/core/mount_facade.py` | readonly-Pläne, Validierung |
| Safety | `backend/core/safety_facade.py` | write_guard-Wrapper |

## Regel

Neue Rescue-/Stick-Features **dürfen keine** zweiten Parser oder Write-Guards einführen. Erweiterungen nur in Facades + dokumentierte Diagnosis-Codes.

## Tests

`test_core_storage_facade_v1.py`, `test_core_mount_facade_v1.py`, `test_core_safety_facade_v1.py`
