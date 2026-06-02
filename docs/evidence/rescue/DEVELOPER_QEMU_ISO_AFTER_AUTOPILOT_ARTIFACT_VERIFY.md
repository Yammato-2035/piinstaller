# Developer-QEMU ISO After Autopilot — Artifact Verify

**Datum:** 2026-06-03

## ISO

| Feld | Wert |
|------|------|
| ISO vorhanden | **yes** |
| ISO-Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| ISO-Größe | `511705088` Bytes (488 MiB) |
| ISO-SHA256 | `614cc86ea865608f68524ef6d905a3baa1c0b1ce3dacaa9f1b80de6f541e0784` |
| file type | ISO 9660 CD-ROM filesystem data (DOS/MBR boot sector) `SETUPHELFER_RESCUE` (bootable) |

## SHA-Vergleich

| Referenz | SHA256 |
|----------|--------|
| Standard-ISO (vorher) | `505989f7d348265c08e8baeaa2971f81aa855224223859ae8d536b984dafaf52` |
| Developer-QEMU vor Autopilot-Fix | `3ee02b364bf5a35106591b67fb975f0864390cb413088c0d000e54e770dd48c1` |
| **Aktuell (nach Fix)** | `614cc86ea865608f68524ef6d905a3baa1c0b1ce3dacaa9f1b80de6f541e0784` |

| Kriterium | Ergebnis |
|-----------|----------|
| SHA neu gegenüber altem Developer-QEMU-ISO | **yes** (≠ `3ee02b36…`) |

**Status:** `ok`

SHA-Datei: `docs/evidence/runtime-results/rescue/developer_qemu_iso_after_autopilot_success.sha256`
