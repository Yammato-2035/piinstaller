# Controlled ISO Build — Safety Precheck

**Stand:** 2026-06-02  
**Status:** **ok**

## Dieser Precheck-Lauf

| Guard | Status |
|-------|--------|
| ISO-Build / lb build | **nicht ausgeführt** |
| mount/umount/chroot | **nicht ausgeführt** |
| apt install | **nicht ausgeführt** |
| USB/dd/mkfs | **nicht ausgeführt** |

## Build-Wrapper

`run-controlled-iso-build-with-logging.sh`: explizit **USB write, dd, mkfs, parted: FORBIDDEN**.

QEMU/USB: separate Skripte mit `--operator-confirm-*` — **nicht** in diesem Precheck.

## Schreibscope Build (wenn freigegeben)

Nur Build-Tree + Evidence-Logs unter `build/rescue/`.

## USB später

Operator-Doppelbestätigung erforderlich (Runbook `usb_write_allowed: false`).
