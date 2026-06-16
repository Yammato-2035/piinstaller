# R.5 — ISO Summary (Preload)

**Version:** 1.7.17.0  
**HEAD:** 57e30d9

## ISO (aktuell im Workspace)

| Feld | Wert |
|------|------|
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| SHA256 | `c9de3751f7fafe51c836d112bac99331c06252a01430b41f2a50b432ca63f194` |
| Build-Status | **stale** — vor R.4, Gate A nicht ausgeführt |
| SquashFS Kiosk-Stack | **red** — fehlt (siehe R5_SQUASHFS_INSPECTION.md) |
| GRUB Assets (Staging) | **green** |
| GRUB grub.cfg (fertig) | **yellow** — pending lb build |
| Browser/Kiosk (Image) | **red** — pending neuer Build |
| Telemetrie-Spool (Image) | **red** — R.3-Skripte nicht im stale SquashFS |

## Erwartete Stick-Evidence nach MSI-Boot

```text
/setuphelfer-evidence/
  boot/
  menu/
  hardware/msi_diagnostics_latest.md
  rescue-ui/kiosk_report_latest.json
  matrix/rescue_test_matrix_latest.md
  telemetry/spool/
  summaries/rescue_evidence_latest.md
```

## USB-Write

**Blockiert** bis Gate B + neues ISO mit grünem SquashFS-Check.
