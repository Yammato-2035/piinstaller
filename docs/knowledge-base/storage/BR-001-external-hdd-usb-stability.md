# BR-001 — Externes HDD / USB / I-O-Stabilität

## Kurzfassung

Der Full-Root-Abbruch (**`BACKUP-IO-ERROR-050`**) wurde durch **USB-Trennung unter Schreiblast** verursacht, nicht durch Backup-Logik oder gzip allein. Kompression lief als **single-threaded gzip** (`pigz` nicht installiert).

## Kompression (gzip vs pigz)

| | |
|--|--|
| **Aktiv im Lauf** | `gzip` via `tar -czf` |
| **pigz** | Code unterstützt `pigz -4` (Desktop) / `-2` (Pi), wenn `which pigz` — **auf diesem Host: nein** |
| **Parallel** | **Nein** (1 gzip-Stream) |
| **Peak Backup-Durchsatz** | ~18 MiB/s (Job `f4269a25a421`) |
| **Stabilitätstest dd** | ~110 MiB/s (15 GiB, 139 s) — USB/Platte nicht der Engpass im Kurztest |

**Entscheidung:** gzip beibehalten; kein pigz-Zwang in dieser Phase. Optional später: pigz mit Thread-Limit dokumentieren.

Implementierung: `backend/core/backup_archive_options.py` → `resolve_compression_choice()`, `build_full_root_tar_command()`; Runner: `_run_tar_pipeline_from_preflight()`.

## Hardware (aktuell)

- **Platte:** HGST HTS721010A9E630, 1 TB, **rotational** (`ROTA=1`)
- **Gehäuse:** SABRENT USB-UAS (`ID_USB_DRIVER=uas`)
- **SMART:** PASSED; `UDMA_CRC_Error_Count=0`; keine pending/reallocated Sektoren; ~31 °C

## Kernel Root Cause (Failure-Lauf)

Zeitfenster **19:55:20–19:55:43** (Evidence `capture_journal_kernel_tail.txt`):

1. `usb 1-2.1: reset` → Descriptor-Fehler **-110 / -71**
2. `USB disconnect, device number 3`
3. `device offline error, dev sda` (WRITE)
4. `EXT4-fs` I/O / Journal abort → read-only remount
5. Backup: `gzip: stdout: Input/output error`

**Korrelation:** Backup schrieb auf `setuphelfer-back1` (~6,8 GiB); Gerät hing an **USB-Hub-Pfad `1-2.1`**, nicht am aktuellen `usb6`-Pfad.

## Nach Disconnect

- Partition neu: UUID **`44ce6f76-…`** (vorher `adbd53e5-…`), praktisch leer — **fsck/mkfs oder Neuformatierung** nach Crash.
- Alte `.partial`/Archive auf alter Partition **nicht** mehr verfügbar.

## Stabilitätstest (2026-05-15 22:02)

- **15 GiB** sequentiell nach `/media/gabriel/setuphelfer-back1` (`dd` + `fdatasync`)
- **Erfolg**, Mount stabil, keine Kernel-Fehler im Fenster (User-Journal)
- Testdatei danach entfernt

## Empfohlene Maßnahmen vor Full-Retry

1. **USB:** Direkt an Root-Port (xHCI), **kein** instabiler Hub wie `usb 1-2.1`; externes Netzteil am Dock falls vorhanden.
2. **Kabel** tauschen; UAS beibehalten; optional dokumentierter `usb-storage` Workaround nur bei wiederholten UAS-Resets.
3. **Mount:** `setuphelfer-back1` konsistent; `fsck` nach Stromverlust vor großem Backup.
4. **Last:** Während Full-Backup keine parallelen `apt-get`/Upgrades; Dashboard-`apt list` blockiert Backup nicht mehr (read-only ausgenommen).
5. **Monitoring:** `journalctl -kf` während Langlauf.

## Full-Retry

**Noch nicht starten** in dieser Aufgabe. Retry sinnvoll, wenn USB-Topologie geändert und 15 GiB-Test wiederholt grün.

Maschinell: `docs/evidence/runtime-results/BR-001-storage-io-stability-2026-05-15.json`
