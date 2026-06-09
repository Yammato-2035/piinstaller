# RS-001 React Shell Launcher — SquashFS Content Check

**Datum:** 2026-06-09  
**Version:** `1.7.10.1`  
**SquashFS:** `build/rescue/filesystem.squashfs.repacked-1.7.10.1`  
**SHA256:** `0b303d3ab563f4aeaa354813dcbf46e8fb934a3f23d4705251129f80f2ac51dc`  
**Quelle:** `filesystem.squashfs.repacked-1.7.10.0` (`a54aae1d…`)

## Pflichtbefund

| Prüfung | Ergebnis |
|---------|----------|
| Version | **1.7.10.1** |
| React UI vorhanden | **yes** |
| rescue.html vorhanden | **yes** |
| setuphelfer-rescue-ui-launch vorhanden | **yes** |
| fallback_tui vorhanden | **yes** |
| rescue-ui-status.json write path | **yes** (`/run/setuphelfer/rescue-ui-status.json`) |
| network-onboarding boot-skip | **yes** (`SKIPPED_BOOT_WAIT_USER`) |
| telemetry default skipped | **yes** (`telemetry_disabled_or_no_consent`) |
| wait-online nicht Boot-Blocker | **yes** (Drop-in `ExecStart=/bin/true`) |
| network/telemetry Boot-Autostart | **no** (wants-Symlinks entfernt) |
| browser/kiosk hard dependency | **no** |
| no_fake_green | **yes** |

## Verify-Report (Auszug)

```json
{
  "contains_react_rescue_shell": true,
  "contains_rescue_ui_launcher_fix": true,
  "contains_fallback_tui": true,
  "contains_network_boot_skip": true,
  "contains_telemetry_default_skipped": true,
  "contains_wait_online_neutralization": true,
  "network_boot_autostart": false,
  "telemetry_boot_autostart": false
}
```

## Stick-Status

Payload-Update auf `/dev/sdb` **ausstehend** (Agent: `sudo` Passwort erforderlich — Operator-Aktion).
