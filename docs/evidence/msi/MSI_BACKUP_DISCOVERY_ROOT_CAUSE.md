# MSI Backup Discovery Root Cause

**Datum:** 2026-06-24  
**Version:** `1.9.16.1`  
**Scope:** Analyse + Fix (kein Backup/Restore ausgeführt)

## Symptom

Backup-Quelle bleibt gelb/rot. Benutzer muss EFI-, Windows- und Recovery-Partitionen einzeln wählen. Kein automatisches „Windows-System“ als Backup-Kandidat.

## Ist-Stand (Phase 0)

| Bereich | Pfad |
|--------|------|
| Discovery Backend | `backend/core/rescue_storage_discovery.py` |
| Plan-Contract | `backend/core/rescue_backup_plan_contract.py`, `backend/core/msi_windows_image_backup.py` |
| GUI | `frontend/src/rescue/RescueBackupPanel.tsx` |
| API | `GET /api/rescue/storage/discovery`, `POST /api/rescue/backup/full-plan` |
| Letzter MSI-Feldnachweis | P3S 2026-06-21 — Discovery HTTP 200, manuelle Quellwahl erforderlich |

## Partition-Analyse (typisches MSI-Layout)

| Device | Typ | Rolle | Backup-fähig (alt) | Problem |
|--------|-----|-------|-------------------|---------|
| `/dev/nvme0n1p1` | vfat | EFI | Einzelkandidat | Technische Partition, nicht gruppiert |
| `/dev/nvme0n1p3` | ntfs | Windows | Einzelkandidat | Größe nur Partition, nicht System |
| `/dev/nvme0n1p4` | ntfs | Recovery | Einzelkandidat | Irreführend als Quelle |
| `/dev/nvme0n1` | disk | Windows-System | Kandidat, aber nicht bevorzugt | Auto-Selection wählte oft USB |
| `/dev/sda*` | usb | Rettungsstick | Falsch als Quelle gewählt | **Haupt-Bug Auto-Selection** |

## Root Cause

1. **Auto-Selection priorisierte USB vor Windows** — `RescueBackupPanel`: `usbPart || usbDisk || winPart` wählte Rettungsstick-/USB-Partitionen.
2. **Keine Windows-Gruppierung** — Discovery lieferte flache Partitionen statt eines `Windows-System`-Kandidaten (EFI+Windows+Recovery).
3. **`source_unknown` im Plan** — `validate_source_target_pair` ignorierte explizite `source_role` aus der GUI.
4. **Plan gelb/rot bei falscher Quelle** — USB-Quelle → `external_test` / blockiert; Partition statt `/dev/nvme0n1` → falscher Scope/Größe.

## Fix (Phasen 4–5)

### Backend — Windows-Gruppierung

- `build_system_source_candidates()` gruppiert `windows_system_disk` mit Tags `efi`, `windows`, `recovery`.
- `system_source_candidates` + gefilterte `source_candidates` (Partitionen der Gruppe ausgeblendet).
- `pick_auto_backup_source()` für API/Tests.

### Frontend — Auto-Selection

- `frontend/src/rescue/backupSourceSelection.ts` — `pickAutoBackupSource`, `sortBackupSources`.
- Rettungsstick/USB wird nicht mehr bevorzugt.
- Ein eindeutiges Windows-System wird automatisch vorausgewählt.
- Backup-Plan wird einmal automatisch nach Discovery geprüft.

### Plan-Contract

- `validate_source_target_pair` respektiert `source_role` aus Payload.
- `build_rescue_full_backup_plan` übergibt `source_role`, `source_type`, `source_fstype`.

## Validierung (Phase 6)

| Szenario | Ergebnis |
|----------|----------|
| MSI-Tree (EFI+Windows+Recovery+Stick+Backup-HDD) | `pick_auto` → `/dev/nvme0n1` `system_group`, Score 100 |
| Partitionen p1/p3/p4 in UI-Liste | **Ausgeblendet** (in Gruppe enthalten) |
| Rettungsstick sda1 | **Nicht** auto-gewählt |
| Plan mit `/dev/nvme0n1` + Rolle | `source.scope=system_disk`, kein `source_unknown` |
| Plan ohne gemountetes Ziel | `target_missing` (ehrlich **ROT/blockiert**, kein Fake-Grün) |
| Plan mit Mount + Rescue-Boot (simuliert) | Unit: Quelle korrekt; Execute-Gate weiterhin HW-abhängig |

### Pytest

```bash
python3 -m pytest backend/tests/test_rescue_windows_backup_discovery_v1.py \
  backend/tests/test_rescue_ui_api_proxy_v1.py -q
```

**Ergebnis:** 16 passed (2026-06-24, Dev-Host)

## Geänderte Dateien

- `backend/core/rescue_storage_discovery.py`
- `backend/core/rescue_disk_role_classifier.py`
- `backend/core/rescue_backup_plan_contract.py`
- `frontend/src/rescue/backupSourceSelection.ts`
- `frontend/src/rescue/RescueBackupPanel.tsx`
- `frontend/src/rescue/rescueBackupApi.ts`
- `backend/tests/test_rescue_windows_backup_discovery_v1.py`
- `backend/tests/test_rescue_ui_api_proxy_v1.py`

## Status

**GELB** — Discovery/Gruppierung/Auto-Selection per Unit-Test belegt; **GRÜN** auf MSI erst nach Live-Boot mit gemountetem Backup-Ziel und `plan_status=ready` ohne manuelle Partitionswahl.
