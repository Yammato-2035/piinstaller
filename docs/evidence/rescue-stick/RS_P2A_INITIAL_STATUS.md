# RS-P2A Initial Status

**Datum:** 2026-06-18

| Feld | Wert |
|------|------|
| Branch | `main` |
| HEAD | `12daf15` (vor RS-P2A) |
| Version | `1.9.5.0` → `1.9.5.1` |
| Public/Private-Gate | Exit 0 |
| Module-Boundary-Gate | review_required, Exit 0 |
| Runtime-Drift | `/opt` 1.9.2.0, erwartet |
| RS-P1 Squashfs SHA256 | `95a66245d7658ac39e4b641c9b52c2502f3b35d4b3a81d73c90e0e5166e7ca68` |

## MSI-Boot-Befund (vor Fix)

| Feld | Wert |
|------|------|
| grub_menu_visible | false |
| rescue_gui_visible | false |
| text_menu_fallback | true |
| wifi_found | false |
| wifi_rescan_success | false |
| backup_plan_created | false |

```json
{
  "backup_execute_allowed": false,
  "restore_execute_allowed": false,
  "wipe_allowed": false
}
```
