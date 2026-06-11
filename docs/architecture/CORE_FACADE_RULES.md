# Core Facade Rules (Phase A.1 — Freeze)

**Status:** AKTIV (Warn-Phase) — keine Blockierung, keine Migration in A.1.

## Ziel

Zukünftige Module (Backup, Restore, Rescue Stick, Partitionshelfer, Malware Scanner, Cloudserver, Provisioning) dürfen **keine parallele** Storage-/Mount-/Safety-Logik implementieren. Sie nutzen ausschließlich die drei Core-Facades.

## Kanonische Facades

| Facade | Modul | Erlaubte Verantwortung |
|--------|-------|------------------------|
| Storage | `backend/core/storage_facade.py` | Blockgeräte, blkid-Exzerpte, Klassifikation, externe Ziele |
| Mount | `backend/core/mount_facade.py` | findmnt-Inventur, Readonly-Pläne, Mount-Safety (plan-only) |
| Safety | `backend/core/safety_facade.py` | Backup-/Restore-/Partition-Zielvalidierung, Safety-Entscheidungen |

**Contract-Version:** `FACADE_CONTRACT_VERSION = 1` in jedem Facade-Modul.

## Verboten für neue Module (direkt)

Neue Dateien unter `backend/modules/`, `backend/api/`, `backend/rescue/`, `frontend/`-nahen Backend-Routen **dürfen nicht**:

- `subprocess.run` / `Popen` mit `lsblk`, `findmnt`, `blkid` aufrufen
- `from core.safe_device import validate_write_target` (außer in Facade-Implementierung)
- `from safety.write_guard import evaluate_write_target` (außer in `safety_facade.py`)
- Eigene Mount-Planner duplizieren (`plan_readonly_*` außerhalb `mount_facade`)

**Stattdessen:**

```python
from core.storage_facade import get_block_devices, classify_storage_target
from core.mount_facade import build_readonly_mount_plan, validate_not_live_root
from core.safety_facade import validate_backup_target, SafetyContext
```

## Dokumentierte Ausnahmen (Legacy — später migrieren)

| Bereich | Grund | Auslauf |
|---------|-------|---------|
| `backend/app.py` | Monolith-Routen | Router-Extraktion Phase B |
| `backend/core/safe_device.py` | Implementierungskern | Intern hinter Facades |
| `backend/modules/storage_detection.py` | Inspect-Pipeline | Delegation an `storage_facade` |
| `backend/safety/write_guard.py` | Pure Logik aus Inspect | Nur via `safety_facade` |
| Rescue FAT32/ESP (`rescue_fat32_esp_*`) | Hardware-Schreibpfad mit Evidence | Eigener Rescue-Ausnahmeblock |
| `backend/deploy/runner_*.py` | Test-/Runbook-Artefakte | Kein Produkt-API-Pfad |
| `backend/inspect/collector.py` | Inspect-Sammelpunkt | Migriert mit Inspect-Refactor |

## Safety-Kontexte

`SafetyContext` in `safety_facade.py`:

- `live` — laufendes Setuphelfer-System
- `rescue` — Rescue-Stick / Live-ISO
- `partition_helper` — Partitionshelfer-Workbench
- `cloudserver_future` — reserviert für Cloudserver Edition

Jeder Aufruf von `validate_*` / `build_safety_decision` muss den Kontext explizit setzen.

## Boundary-Prüfung

`scripts/check-module-boundaries.sh` meldet **WARNUNGEN** (noch kein CI-Fail) bei:

- Direktem `subprocess` + `lsblk` / `findmnt` / `blkid` außerhalb Allowlist
- Direktem Import von `safe_device.validate_write_target` oder `write_guard.evaluate_write_target` außerhalb Facades/Legacy-Kern

## Nicht in A.1

- Keine API-Änderungen
- Keine Runtime-Migration
- Kein Entfernen von Legacy-Code
- Kein Verschieben von Logik in Facades (nur Contracts + dünne Delegation)

## Nächster Schritt (nach A.1)

Phase A.2: Caller-Migration beginnend mit `partitions` API und `preflight/backup.py` — jeweils ein Modul pro PR, mit Contract-Tests.
