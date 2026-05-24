# Partitions Safety Contracts (Phase 2)

## Ziel

Phase 2 definiert **Sicherheitsverträge** für spätere Partitionierungsaktionen. Es werden **keine** Format-, Resize-, Lösch- oder Restore-Ausführungen aktiviert.

## Storage classification source of truth

| Priorität | Quelle | Nutzung |
|-----------|--------|---------|
| 1 | `core/storage_facade.py` + `modules/storage_detection.py` | Rescue/Live-Inventar, Klassifikations-Flags |
| 2 | `safety/write_guard.py` + `core/safe_device.py` | Write-Target-Bewertung aus Inspect |
| 3 | `apps/partitionshelfer/core/disk_scanner.py` | **Nur** UI-Scan (Phase 1), nicht als Safety-SoT |

Partitions-API `/hardstop-preview` akzeptiert `storage_classification` / Query-Flags vom Aufrufer. Mittelfristig: Backend orchestriert Facade-Ergebnis und übergibt strukturiert (TODO Adapter in Route).

## Partition hardstop layer

Datei: `apps/partitionshelfer/core/partition_hardstop.py`

- `build_partition_hardstop_context` – Kontext ohne Side-Effects
- `evaluate_partition_hardstops` – `status`, `hardstops`, `warnings`, `risk_level`, `codes`
- Immer `write_allowed: false`

### Pflicht-Blockaden

- Ziel fehlt
- Ziel = Backup-Quelle (gleiches Gerät/Disk)
- Systemdisk laut Klassifikation
- SMART failing/critical
- Unbekannte Zielidentität (Write-Kontext)
- Write-Aktion ohne `explicit_write_release` (Zukunft)

## SMART gate (read-only)

- Kein `smartctl` in Partitions-Core
- Adapter: `smart_summary` wie von `modules/inspect_storage.smart_classify_disk`
- missing/unknown → `review_required`
- warning → `review_required`
- failing → `blocked`

## Manifest layout preview

Datei: `apps/partitionshelfer/core/manifest_layout_preview.py`

Liest tolerant `setuphelfer-backup-manifest`:

- `partitions[]`
- `partition_layout_sfdisk_d`
- `entries[]` mit `type: partition`

Output: `original_layout`, `suggested_layout` (Kopie), `write_allowed: false`.

## Restore handoff

Datei: `apps/partitionshelfer/core/restore_handoff_contract.py`

- `handoff_type: partition_to_restore_preview`
- `restore_execution_allowed: false`
- `required_next_gates`: `BACKUP_BEFORE_OVERWRITE_GATE`
- Bei Hardstop `blocked` → Handoff `blocked`

## API (read-only)

| Methode | Pfad |
|---------|------|
| GET | `/api/partitions/hardstop-preview` |
| POST | `/api/partitions/manifest-layout-preview` |
| POST | `/api/partitions/restore-handoff-preview` |

`POST /queue/apply` bleibt Phase-2-Stub.

## Abgrenzung GParted

GParted führt Partitionierung interaktiv aus. Setuphelfer Phase 2 liefert nur **Plan, Preview, Validation** mit festen Hardstops und Produkt-Gates.

## Abbruchkriterien für echte Writes (später)

1. Hardstop `ok` oder explizit freigegebenes `review_required`
2. SMART nicht critical
3. Backup-Quelle ≠ Ziel
4. `BACKUP_BEFORE_OVERWRITE_GATE` bestanden
5. Operator-Bestätigung + Queue-Freigabe außerhalb Phase 2
