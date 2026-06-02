# QEMU Guest Agent Smoke — Serial Review

**Datum:** 2026-06-02

## Status

**QEMU nicht gestartet** — Phase 2 (`local_lab`) blockiert durch fehlendes `sudo` im Agent-Kontext.

| Marker | Gesehen |
|--------|---------|
| Bootloader | **no** |
| Kernel | **no** |
| systemd | **no** |
| Live-System | **no** |
| Setuphelfer-/Agent-Marker | **no** |
| Serial leer | **n/a** (kein Lauf) |

## Bewertung

**Status: blocked** — kein Serial-Log in diesem Lauf.

Referenz (Prior-Lauf ohne local_lab): `QEMU_DEVELOPER_BOOTLOADER_SERIAL_SMOKE_RESULT.md` — ISOLINUX + systemd sichtbar, kein Guest-Report.
