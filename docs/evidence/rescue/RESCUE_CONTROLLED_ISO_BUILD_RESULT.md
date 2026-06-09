# Rescue Controlled ISO Build — Ergebnis

**Datum:** 2026-06-09  
**HEAD:** `dad1db5`  
**Version:** `1.7.10.1`

## Zusammenfassung

| Feld | Wert |
|------|------|
| `build_status` | **success** |
| `controlled_lb_build` | **not_run** (sudo/root nicht erforderlich für Repack) |
| `repack_status` | **success** |
| `build_mode` | `squashfs_repack` |
| `squashfs_path` | `build/rescue/filesystem.squashfs.repacked-1.7.10.1` |
| `squashfs_sha256` | `0b303d3ab563f4aeaa354813dcbf46e8fb934a3f23d4705251129f80f2ac51dc` |
| `source_squashfs_sha256` | `a54aae1d902523cf08b37105b1f6001e048d610b57210520ea2e1a649b3fe820` |

## Launcher-Fix im SquashFS

| Check | Wert |
|-------|------|
| `contains_react_rescue_shell` | true |
| `contains_rescue_ui_launcher_fix` | true |
| `contains_fallback_tui` | true |
| `contains_network_boot_skip` | true |
| `contains_telemetry_default_skipped` | true |
| `contains_wait_online_neutralization` | true |
| `network_required_before_menu` | false |
| `telemetry_required_before_menu` | false |

Evidence: `docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json`
