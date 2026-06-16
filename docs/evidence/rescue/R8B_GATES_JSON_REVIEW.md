# R.8B — Gates JSON Review

**Datum:** 2026-06-13

## Gates-Quelle

Kein separates `gates.json` auf Platte — Gates werden zur Laufzeit von `validate_fat32_execute_write_gates()` ausgegeben (stdout vor Exit 28).

Zusätzlich: `plan.json` im Dry-run / Write-Vorbereitung.

| Artefakt | Pfad |
|----------|------|
| Execute-Gates (blockiert) | Skript-stdout / unten |
| Plan (dry-run) | temporär; Referenz `fat32_esp_write_20260613_211315/plan.json` |
| Operator-Selection | `docs/evidence/runtime-results/rescue/usb_operator_selection_latest.json` |

## Gates JSON (blockiert — Stick gemountet)

```json
{
  "blocked": true,
  "blockers": ["TARGET_DEVICE_MOUNTED", "TARGET_PARTITION_MOUNTED"],
  "errors": ["target_device_mounted", "target_partition_mounted"],
  "write_allowed": false,
  "iso_sha256": "18d613e569da4b322f962a1928054d5660280a7ab9626302d2100d3150760390",
  "expected_iso_sha256": "18d613e569da4b322f962a1928054d5660280a7ab9626302d2100d3150760390",
  "staging_complete": true
}
```

## Gates JSON (nach Unmount — gates green)

```json
{
  "blocked": false,
  "blockers": [],
  "write_allowed": true,
  "iso_sha256": "18d613e569da4b322f962a1928054d5660280a7ab9626302d2100d3150760390",
  "staging_complete": true
}
```

## Pflichttabelle

| Gate | Wert (initial) | Erwartet | Status | Ursache |
|------|----------------|----------|--------|---------|
| `execute_write` | true | true | OK | Flag gesetzt |
| `confirm_write` | true | true | OK | `--operator-confirm-write` |
| `confirm_phrase` | exakt | `WRITE SETUPHELFER FAT32 ESP USB` | OK | Match |
| `iso_sha256` | `18d613e5…` | `18d613e5…` | OK | R.8 ISO |
| `staging_complete` | true | true | OK | Staging vorhanden |
| `target` `/dev/sdb` | disk | disk (nicht Partition) | OK | Korrektes Gerät |
| `target_not_internal` | usb | usb | OK | TRAN=usb |
| `target_not_backup` | ja | ja | OK | sda=Backup, sdb=Rescue |
| `target_not_root` | ja | ja | OK | nvme=root, sdb≠root |
| **`target_not_mounted`** | **nein** | ja | **FAIL** | `/dev/sdb1` → `/media/.../SETUPHELFER` |
| `operator_evidence` | write_allowed | true | OK | `usb_operator_selection_latest.json` |
| `operator_confirmations` | alle true | complete | OK | 5/5 |
| `OPERATOR_USB_WRITE_FREIGABE` env | unset | 1 (Workflow) | **WARN** | Nicht im Skript enforced |

## Operator-Selection Hinweis

`usb_operator_selection_latest.json` enthält **veraltete** `iso_sha256` (älterer Build). Gate **ISO_SHA256_MISMATCH** trat **nicht** auf, weil `--expected-iso-sha256` korrekt gesetzt wurde und gegen **aktuelle** ISO-Datei geprüft wird.
