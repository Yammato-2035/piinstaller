# BR-001 Phase 2 — Full-Root-Backup Langlauf (2026-05-15)

## Ergebnis: **failed** (rot)

Kein vollständiges Full-Root-Archiv. Kein Deep-Verify. Echte Langlauf-Daten und echte Fehler dokumentiert.

## Phase 0

Gate grün, `safe_test_mode=UNLOCKED`.

## Zielmedium (vor Lauf)

| | |
|--|--|
| Gerät | `/dev/sda1` |
| Mount | `/media/gabriel/setuphelfer-back1` |
| UUID | `adbd53e5-26fd-4723-b0f1-1880dbaa2719` |
| Frei | ~679 GiB |

## Preflight-Excludes (Full `/`)

`/proc`, `/sys`, `/dev`, `/tmp`, `/run`, `/mnt`, `/media`, `/run/media`, Backup-Zielverzeichnis, Profil `full-expert`-Zusatzexcludes. Kompression: `gzip` (tar `-czf`). `systemd-inhibit`: aktiv.

## Läufe

### 1–2: `backup.blocked_package_activity` (12 s / 48 s)

Während `tar` lief parallel **`apt list --upgradable`** (aus `get_updates_categorized()` → Dashboard `/api/system/status`). Runner brach konservativ ab (`UPDATE-CONFLICT-041`).

**Fix (Präzision, kein Lock-Removal):** `core/package_activity.py` — read-only `apt list` / `apt-cache` blockieren nicht mehr; `apt-get`/`dpkg`/Upgrade weiterhin blockierend.

### 3: Langlauf `f4269a25a421` (~8,7 min)

- **Start:** 19:46:59 CEST  
- **Peak:** ~6,8 GiB `.partial`, ~18 MiB/s  
- **Ende:** `backup.write_io_error` / `BACKUP-IO-ERROR-050`  
- **stderr:** `gzip: stdout: Input/output error`  
- **Danach:** `/dev/sda` in `lsblk` **weg**, Mount `setuphelfer-back1` **fehlt** → USB-/Gerätetrennung während Schreiblast.

`.partial` wurde **nicht** gelöscht (`partial_deleted: false`); nach Reconnect Bereinigung nötig.

## Verify

Nicht ausgeführt (kein fertiges `.tar.gz`).

## Governance

Backup/Restore/Rescue bleiben rot/gelb — kein Fake-Grün.

## Nächste Schritte (Betreiber)

1. Externes Laufwerk stabil reconnecten und mounten  
2. `.partial`-Altlast prüfen/löschen  
3. Full-Backup erneut (Timer/apt-get-Fenster beachten)  
4. Nach Erfolg: Verify deep → Restore Preview  

JSON: `BR-001-full-root-longrun-2026-05-15.json`
