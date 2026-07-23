# LAST_BOOT_095959Z_ANALYSIS — PI-RS-ASUS-LAB-CONTROL-006

## Beobachtet (belegt)

| Feld | Wert |
|------|------|
| Run | `hw-discovery-20260723T095959Z-5317559d` |
| Payload | `1.10.2.9` |
| Zielrechner | ASUSTeK ROG Strix G513QM (`board_name=G513QM`, BIOS `G513QM.331`) |
| machine_id | `79396619c22d7b85a9fe12605be514de731c157ba349911edfa65df5017b38b9` |
| NTFS-Mount | `mounted_ro` via Bookworm `ntfs-3g` |
| ntfs3 | Kernel: `unknown filesystem type 'ntfs3'` (CONFIG_NTFS3_FS unset) |
| Früherer GLIBC-2.38-Fehler | **nicht** mehr vorhanden |
| Panther-Dateien | **0** |
| Rollback-Dateien | **0** |
| scan_status | `insufficient_evidence` |
| windows_setup_logs | `not_found` |
| Auto-Capture | lief (`verdict=LOGS_FEHLEN`) |
| WinPE früher | `unknown-norunid`, leer |
| Windows-Layout | MSR + große NTFS Basic data (`nvme0n1p2`) |
| Linux-NVMe | GPT ohne Partitionen (Rolle lab relevant) |

## Abgeleitet

- Der NTFS-Mount-Tooling-Fehler ist **nicht** mehr die Ursache fehlender Logs.
- Ein erneuter rein nachträglicher Panther-Scan liefert voraussichtlich keine neuen Setup-Artefakte, solange Setup keine Pfade persistiert.

## Unbekannt

- Ob Setup überhaupt weit genug lief, um Panther persistent anzulegen.
- Ob Logs nur in RAM/X: lagen und beim Hang verloren gingen.
- Ob ein anderer Volume-Pfad existierte, der nicht gescannt wurde.

## Nicht zulässig (nicht behauptet)

- „Windows Setup hat definitiv vor Panther abgebrochen“ — ohne Live-Evidence unbewiesen.
- BIOS 335 als Ursache/Fix — ohne Setup-Artefakte und ohne Preflight nicht begründbar.

## Folge

Kritischer Pfad: **instrumentierte Live-Capture während Setup** (Pfad A), nicht erneuter Post-Hang-only Scan.
