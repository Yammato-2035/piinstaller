# R.8B — USB Gate Root Cause

**Datum:** 2026-06-13

## Klassifikation

# **D — target_mounted**

Primärer Blocker:

- `TARGET_DEVICE_MOUNTED`
- `TARGET_PARTITION_MOUNTED`

`/dev/sdb1` war unter `/media/gabriel/SETUPHELFER` eingehängt (rw), vermutlich nach Dev-Rechner-Inspection des alten Sticks.

## Sekundär (Agent-Umgebung)

**I — execute_requires_operator_tty** (nach Gate-Freigabe)

Alle destruktiven Schritte nutzen `sudo` (`wipefs`, `sgdisk`, `mkfs.vfat`, …). In Agent-Shell: `sudo: Ein Passwort ist notwendig` → **kein** erfolgreicher Write.

## Ausgeschlossen

| Klasse | Status |
|--------|--------|
| A operator_env_missing | Env unset, aber **nicht** script-enforced; Operator-Evidence OK |
| B wrong_target_device | **nein** — `/dev/sdb` korrekt |
| C target_is_partition | **nein** — `/dev/sdb1` wäre falsch (separat dokumentiert) |
| E target_not_removable | **nein** — usb |
| F target_is_backup_disk | **nein** — sda=Backup, Target=sdb |
| G iso_sha_mismatch | **nein** — SHA match R.8 |
| H confirm_phrase_mismatch | **nein** |
| J script_bug | **nein** — Mount-Check korrekt |

## Fix (keine Gate-Abschwächung)

1. Stick **unmounten** vor `--execute-write`
2. Write im **Operator-Terminal** mit **sudo** (interaktiv)
3. Optional Workflow-Env setzen:
   ```bash
   export OPERATOR_USB_WRITE_FREIGABE=1
   export USB_TARGET=/dev/sdb
   export USB_TARGET_CONFIRMED=1
   ```
4. `usb_operator_selection_latest.json` ISO-SHA auf R.8 aktualisieren (DCC/Operator — nicht zwingend für Gate wenn `--expected-iso-sha256` gesetzt)

## Status nach Diagnose-Unmount

Gates **green**, aber Write in Agent-Umgebung an **sudo** gescheitert — Stick-Inhalt **unverändert** (alte Squashfs).
