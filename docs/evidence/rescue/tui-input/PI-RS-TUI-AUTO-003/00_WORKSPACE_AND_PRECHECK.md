# 00 – Workspace und Precheck

## Workspace

| Feld | Wert |
|------|------|
| Pfad | `/home/volker/piinstaller` |
| Branch | `pi-rs-e2e-live-001d-physical-backup-restore` |
| HEAD | `bd3c529c76f8d276b1fc099f4c18230e6efdd3af` |
| origin/main | `b8651d3337bf30b4443a622fdf8a6c9dc2995df5` |
| AUTO-001 Ancestors | ja (`4535f647`, `30aa68b8`) |
| AUTO-002 Evidence | ja (`7acc9bf2` … `bd3c529c`) |
| Remote Branch | vorhanden, = lokal |
| Drift | ~70 Dateien (fremde Lab-Drift) — **nicht** angefasst |

## Stick Preboot

| Feld | Wert |
|------|------|
| Gerät | `/dev/sda` (eindeutig, 1 Kandidat) |
| Modell | Intenso Ultra Line |
| Größe | ~59G |
| Labels | SETUPHELFER + SETUP_LOGS |
| Root | `/dev/nvme1n1p2` — nicht USB |
| Payload VERSION | **1.10.0.59** |
| SquashFS | `3706b824…ef43e` |
| GRUB | `68649d4d…931030` |
| Diagnoseeintrag | vorhanden |
| Default | `set default=0` (nicht Diagnose) |
| Auto-Shutdown | `setuphelfer_tui_input_diag_auto_shutdown=0` |
| Existing diag runs on SETUP_LOGS | **keine** |

## Status

`precheck_passed` — bereit für physischen MSI-Lauf.  
Import/Analyse: **pending_operator**.
