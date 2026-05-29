# Rescue ISO — Build-Tree-Verifikation (Runtime Integration)

**prepare:** Exit 0  
**Manuelle Pflichtchecks:** alle **grün**

- `keyboard_file=1`, `XKBLAYOUT="de"`
- `vconsole_file=1`, `KEYMAP=de-latin1`
- `locale_file=1`, `LANG=de_DE.UTF-8`
- `timezone_file=1`, `Europe/Berlin`
- `multi-user.target.wants` → `setuphelfer-backend.service`, `setuphelfer.service`
- `auto/config` → hostname, username, keyboard-layouts, locales, timezone

**Hinweis:** `validate-controlled-live-build-tree.sh` meldet **FORBIDDEN** `binary/live/filesystem.squashfs` solange ein alter `lb build` im Tree liegt. Vor Operator-Rebuild: `lb clean` / `auto/clean` wie Runbook.

**Alte ISO:** `validate-rescue-iso-squashfs.sh` → Exit **12** (systemd enable fehlt).

JSON: `rescue_iso_runtime_integration_build_tree_verification_latest.json`
