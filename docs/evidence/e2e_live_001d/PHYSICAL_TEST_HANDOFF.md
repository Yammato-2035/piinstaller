# SETUPHELFER-E2E-LIVE-001D3A — Physical Test Handoff

| Feld | Wert |
|------|------|
| Feature | `SETUPHELFER-E2E-LIVE-001D3A` |
| Payload-Version | `1.10.0.22` |
| Payload-SHA256 | `9190460c3aa785252eaa4aef51569b9ab103fca24997e0bc941f59b7835bac4e` |
| Stick | Intenso Ultra Line `/dev/sda` |
| SETUPHELFER UUID | `9BB9-A4A6` |
| SETUP_LOGS UUID | `9BC7-3950` (unverändert) |
| Unattended Service | `setuphelfer-rescue-auto-physical-e2e` |
| GRUB MSI-Lab-Auto | aktiv (`setuphelfer_msi_lab_auto=1`) |
| GRUB MSI-E2E-Auto | aktiv (`setuphelfer_msi_e2e_auto=1`) |
| Auto-Shutdown | nach E2E (`setuphelfer_auto_shutdown=1`) |
| production_ready | `false` |
| Status | `implemented_pending_unattended_msi_run` |

## Boot-Reihenfolge (systemd)

1. `setuphelfer-rescue-auto-msi-evidence.service` — MSI RS-011B Evidence (Late Gate 120s)
2. `setuphelfer-rescue-auto-physical-e2e.service` — Unattended Physical E2E
3. Evidence-Spool-Sync (via Service-Kette)
4. Shutdown nach E2E-Abschluss (GRUB `setuphelfer_auto_shutdown=1`)

## Operator-Schritte (MSI GE63)

1. Vom Stick booten — MSI/NVIDIA-Kompatibilitätsmodus ist erster GRUB-Eintrag (timeout 3s)
2. Payload-Version `1.10.0.22` auf TTY1/Backend prüfen
3. Lab-Token **nicht** in Payload — zur Laufzeit unter `SETUP_LOGS/setuphelfer/lab/telemetry-lab-token` bereitstellen (optional für Telemetry-Send)
4. Unbeaufsichtigter Lauf: Evidence → E2E → Sync → Shutdown
5. Nach Reboot: Evidence importieren mit `scripts/rescue/import-e2e-live-001d-evidence.sh`

## Bekannte Vorläufe (nicht überschreiben)

- Dev-Lab-Lauf `e2e-rescue-physical-20260714-153401-d35375d0` bleibt auf SETUP_LOGS erhalten

## Evidence-Artefakte

- `docs/evidence/e2e_live_001d/unattended_payload_version_selection.json`
- `docs/evidence/e2e_live_001d/unattended_payload_build.json`
- `docs/evidence/e2e_live_001d/unattended_usb_update.json`
- `docs/evidence/e2e_live_001d/grub_msi_auto_e2e_verification.json`
