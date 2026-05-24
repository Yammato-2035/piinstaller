# Partitionshelfer Phase 2 – Safety-Analyse (Ausgangslage)

**Datum:** 2026-05-23  
**HEAD:** `7759658` (vor Phase-2-Implementierung)

---

## Scan-Quelle

| Komponente | Quelle |
|------------|--------|
| API `GET /scan` | `apps/partitionshelfer/core/disk_scanner.py` → `lsblk --json` (read-only subprocess) |
| Phase-1 UI/tkinter | gleicher Core |

**Eigene lsblk-Duplikate im Partitionshelfer:** nur in `disk_scanner.py` (bewusst für UI-Scan).  
**Backend:** `core/storage_facade.py`, `core/safe_device.py`, `modules/storage_detection.py` – separate Pfade für Produkt-Safety.

---

## Queue / apply (aktuell)

- `backend/api/routes/partitions.py`: In-Memory-`_queue`, `POST /queue/apply` gibt immer `erfolg: 0` und Phase-2-Stub-Message.
- Keine mkfs/parted/dd in Route.

---

## Wiederverwendbare Safety-Bausteine (Backend)

| Modul | Rolle |
|-------|--------|
| `safety/write_guard.py` | `evaluate_write_target` aus Inspect-Daten |
| `core/safe_device.py` | Allowlist, `validate_write_target`, Klassifikation |
| `core/storage_facade.py` | read-only lsblk-Envelope, `classify_storage_devices` |
| `modules/inspect_storage.py` | `smart_classify_disk` (smartctl -H, read-only) |
| `core/rescue_hardstop.py` | Restore-Hardstops inkl. Quelle=Ziel |
| `modules/backup_engine.py` | Manifest `partition_layout_sfdisk_d` |

Phase 2 nutzt **Adapter-Schnittstellen** (Parameter `storage_classification`, `smart_summary`) statt paralleler lsblk-Pipelines in neuen Core-Dateien.

---

## Später gefährliche Funktionen (nicht aktivieren)

- `disk_scanner` + direkte parted/sfdisk-Aufrufe
- `queue/apply` mit echter Ausführung
- Backup-Runner `create_manifest` / `sfdisk -d` (nur Backup-Kontext, nicht Partitions-UI)

---

## Phase-2-Lieferumfang (Plan)

1. `partition_hardstop.py` – Hardstop-Codes, `write_allowed: false`
2. SMART-Gate über Summary-Adapter (kein smartctl in Core)
3. Backup-Quelle ≠ Partitionierungsziel
4. `manifest_layout_preview.py` – Layout-Vorschau
5. `restore_handoff_contract.py` – Restore-Preview-Handoff only
6. API read-only Endpunkte
7. Tests + Evidence
