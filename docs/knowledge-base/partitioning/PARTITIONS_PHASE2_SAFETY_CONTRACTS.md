# Partitionshelfer Phase 2 – Safety Contracts (Kurz)

## Was Phase 2 tut

- Hardstops für Partitionierungs**ziele** definieren
- Backup-Quelle darf **nie** Ziel sein
- SMART nur als **Gate** (über übergebene Daten, kein smartctl im Partitions-Core)
- Layout-Vorschlag aus Backup-Manifest (**Preview**)
- Restore-Handoff als **Vorschau** (kein Restore-Start)

## Was Phase 2 nicht tut

- Kein mkfs, parted, sfdisk, wipefs, dd
- Kein mount/umount für Partitionierung
- Kein Backup/Restore starten
- Kein Queue-Apply mit echten Writes

## API

- `GET /api/partitions/hardstop-preview`
- `POST /api/partitions/manifest-layout-preview`
- `POST /api/partitions/restore-handoff-preview`

Alle Antworten: `write_allowed: false`.

## Tests lokal

```bash
PYTHONPATH=backend backend/venv/bin/python3 -m pytest \
  backend/tests/test_partitions_api_v1.py \
  backend/tests/test_partitions_phase2_safety_contracts_v1.py -q
```

## UI Preview

- Seite: Partitionen (`PartitionManager`)
- Panel: `PartitionSafetyPreviewPanel` (read-only)
- Lädt bei Partition-Auswahl:
  - `GET /api/partitions/hardstop-preview`
  - `POST /api/partitions/manifest-layout-preview` (manifest=null)
  - `POST /api/partitions/restore-handoff-preview`
- Evidence: `docs/evidence/partitions/PARTITIONS_PHASE2_UI_PREVIEW_STUB.md`

## Weiterführend

- Architektur: `docs/architecture/PARTITIONS_SAFETY_CONTRACTS.md`
- Analyse: `docs/evidence/partitions/PARTITIONS_PHASE2_SAFETY_ANALYSIS.md`
- Evidence: `docs/evidence/partitions/PARTITIONS_PHASE2_SAFETY_CONTRACTS.md`
