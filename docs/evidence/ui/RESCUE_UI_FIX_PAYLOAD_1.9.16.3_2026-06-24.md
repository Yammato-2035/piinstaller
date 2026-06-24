# Rescue UI Fix Payload 1.9.16.3 (2026-06-24)

## Version

- **project_version:** 1.9.16.3 (Bugfix W)
- **Vorgänger:** 1.9.16.2

## Payload

| Artefakt | Pfad | SHA256 |
|---|---|---|
| SquashFS | `build/rescue/filesystem.squashfs.repacked-1.9.16.3` | `3bc4558995092e1ea59264a69a5a0a23221d871be7a150b150357c03e9584fc6` |

## Enthaltene Fixes

1. **Startmenü-Layout:** `RescueShellLayout` + `RescueDashboard`, korrektes `onSelectTile`-Routing
2. **CSS:** Tile max-width 520px, Grid max 1100px, sticky Toolbar, Logo 220px @768h
3. **Screenshot-Evidence:** `POST /api/rescue/ui/screenshot`, `scripts/rescue-live/capture-rescue-screenshot.sh`
4. **Safe-Walk:** `?safe_walk=1` / `RESCUE_UI_SAFE_WALK=1` blockiert Shutdown/Reboot/DataRescue-Execute

## Tests (Workspace)

```bash
cd backend && ./venv/bin/python -m pytest \
  tests/test_rescue_ui_screenshot_v1.py \
  tests/test_rescue_react_ui_contract_v1.py \
  tests/test_rescue_gui_visual_contract_v1.py \
  tests/test_linux_migration_assistant_contract_v1.py \
  tests/test_rescue_windows_backup_discovery_v1.py -q
# 45 passed
```

Rescue React Build: `build/rescue/ui/assets/rescue-*.js` enthält `rescue-dashboard`.

## Stick-Update (Operator)

Dev-Stick derzeit **nicht angeschlossen** (`/dev/sda` nicht vorhanden).

```bash
sudo ./scripts/rescue-live/update-fat32-esp-live-payload.sh \
  --target /dev/sda \
  --new-squashfs build/rescue/filesystem.squashfs.repacked-1.9.16.3 \
  --operator-confirm-update \
  --confirm-phrase "UPDATE SETUPHELFER FAT32 ESP LIVE PAYLOAD" \
  --execute-update
```

## MSI Live (Operator Phase 10)

1. Boot vom Stick
2. `./scripts/rescue-live/capture-rescue-screenshot.sh start-menu`
3. URL `?safe_walk=1` — alle Tiles öffnen, keine destruktiven Aktionen
4. Erst bei grünem UI: Backup-Discovery prüfen (kein Backup ohne Freigabe)

## Status

| Prüfung | Status |
|---|---|
| Code + Contract-Tests | GRÜN |
| Payload gebaut | GRÜN |
| Stick aktualisiert | ROT (Stick nicht erkannt) |
| MSI Live | GELB (ausstehend) |
