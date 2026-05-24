# Partitions Phase 2 – Safety Contracts (Evidence)

**Datum:** 2026-05-23  
**HEAD:** nach Implementierung (siehe Commit)

---

## Scope

Phase 2: Plan / Preview / Validation only. **Keine Schreiboperationen.**

---

## Neue Core-Dateien

| Datei | Funktion |
|-------|----------|
| `apps/partitionshelfer/core/partition_hardstop.py` | Hardstop-Kontext + Auswertung |
| `apps/partitionshelfer/core/manifest_layout_preview.py` | Manifest → Layout-Preview |
| `apps/partitionshelfer/core/restore_handoff_contract.py` | Restore-Handoff-Preview |

---

## API-Endpunkte

| Methode | Pfad | write_allowed |
|---------|------|---------------|
| GET | `/api/partitions/hardstop-preview` | false |
| POST | `/api/partitions/manifest-layout-preview` | false |
| POST | `/api/partitions/restore-handoff-preview` | false |

Bestehend: `/scan`, `/safety-check`, `/queue`, `/queue/apply` (Stub).

---

## Hardstop-Codes (Auszug)

- `partition.hardstop.target_missing`
- `partition.hardstop.partition_target_is_backup_source`
- `partition.hardstop.target_identity_unknown`
- `partition.hardstop.target_is_system_disk`
- `partition.hardstop.smart_failing`
- `partition.warning.smart_yellow`
- `partition.warning.manual_review_required`
- `partition.info.readonly_phase2`

---

## SMART-Gate

| Status | Ergebnis |
|--------|----------|
| ok | kein SMART-Block |
| warning | review_required |
| missing/unknown | review_required |
| failing | blocked |

Kein smartctl in Partitions-Core; Adapter zu `inspect_storage.smart_classify_disk`.

---

## Tests

```bash
PYTHONPATH=backend backend/venv/bin/python3 -m pytest \
  backend/tests/test_partitions_api_v1.py \
  backend/tests/test_partitions_phase2_safety_contracts_v1.py -q
```

Pflichtfälle: 12+ in `test_partitions_phase2_safety_contracts_v1.py` (Hardstop, SMART, Manifest, Handoff, verbotene Tokens, API/OpenAPI).

---

## Write-Schutz

- Alle Phase-2-Funktionen: `write_allowed: false`
- `restore_execution_allowed: false` im Handoff
- Queue/apply unverändert Stub

---

## Abgrenzung

- GParted: interaktive Ausführung
- Setuphelfer Phase 2: Verträge + Preview für spätere Phasen mit Gates
