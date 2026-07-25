# PI-RS-INSTALL-ASSISTANT-001 — Zug A1 Install-Diagnose

## Issue-Codes

- `bios_outdated_likely`
- `pcie_aer_flood_blocks_installer`
- `secure_boot_blocks_unsigned_iso`
- `wrong_boot_device_selected`
- `nvme_not_visible_in_installer`
- `installer_media_corrupt`
- `disk_role_ambiguous`

## Telemetrie

- Upload nur redigiert: `redact_install_diagnosis_for_upload`
- Pfad-Hinweis: bestehende Assessment-V2-Upload-Pfade (`assessment_v2_redacted`)
- `dry_run_local` in Unit-/API-Tests; keine PII

## Evidence auf Stick

Unter `SETUP_LOGS/.../install-diagnosis/` (Schema: `install_diagnosis_v1` / `install_diagnosis_v1_redacted`).

## UI

Rescue-Panel „Installationsdiagnose“ (Ampel + nächste Aktion) in `RescueLinuxInstallPanel.tsx`.

## Nicht enthalten

Kein BIOS-Flash.
