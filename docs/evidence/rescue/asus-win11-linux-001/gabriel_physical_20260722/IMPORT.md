# Gabriel ASUS ROG — Stick-Import 2026-07-22

## Quelle

- Stick: Ultra Line `/dev/sda`
- Partition: `SETUP_LOGS` → `/media/volker/SETUP_LOGS2`
- Boot-Diagnostik: `20260722_184957_boot`
- Boot-ID: `503549ad-1af5-46fd-bcbb-131aaf5e7b47`
- E2E-Run-ID: `e2e-rescue-msi-20260722-185003-06bf2dea`

## Maschine

| Feld | Wert |
|------|------|
| Produkt | ROG Strix G513QM_G513QM |
| Board | G513QM |
| BIOS | G513QM.331 |
| Dual-NVMe | ja (04:00.0 + 05:00.0 Samsung) |
| Developer-Host G713PI | nein |

## Import-Ergebnisse

1. Auto-Discovery-Import: ok → `docs/evidence/e2e_live_001d/physical_discovery_runs/503549ad-…`
2. Gabriel-Paket (redacted): `docs/evidence/rescue/asus-win11-linux-001/gabriel_physical_20260722/`
3. Offizieller E2E-Import: Run war `blocked` (run_control) — Artefakte trotzdem lokal im Gabriel-Paket

## Diagnose-Status

`diagnosis_incomplete` — fehlt u. a. NVMe SMART/Serienhashes, Win11-Panther, Media-Check, offizieller BIOS-Vergleich, Operator-Gabriel-Bind.
