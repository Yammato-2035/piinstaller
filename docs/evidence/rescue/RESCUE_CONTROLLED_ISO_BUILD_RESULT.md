# Rescue Controlled ISO Build — Result

**Datum:** 2026-05-24 (Retry — tar/adduser)
**Git HEAD:** `83ec644`
**Gesamtstatus:** **ISO_BUILD_FAILED** → **Clean-State bereit, Operator-Build ausstehend**

---

## Retry-Session — Ursache tar/adduser

### Reproduktion (Operator-Terminal, vor Fix)

```
I: Extracting adduser...
E: Tried to extract package, but tar failed. Exit...
LB_EXIT=1
```

### Root Cause (debootstrap.log)

**Kein Dateisystem-Problem.** Build-Verzeichnis liegt auf **ext4** (`/dev/nvme0n1p2`), ~1,3 TB frei.

**Ursache:** **Verunreinigter chroot** aus vorherigem **fakeroot**-Teilbuild + **lb bootstrap cache restore**:

```
tar: ./usr/sbin/adduser: Cannot open: File exists
tar: ./usr/sbin/addgroup: Cannot create symlink to 'adduser': File exists
tar: Exiting with failure status due to previous errors
```

debootstrap versuchte `adduser` erneut zu extrahieren, obwohl Dateien/Symlinks aus partiellem Bootstrap bereits in `chroot/` lagen (Owner `gabriel:workspace`, nicht root).

### Fix (durchgeführt)

| Maßnahme | Status |
|----------|--------|
| `auto/config` → `lb config noauto` | **fixed** (keine Rekursion mehr) |
| `prepare-controlled-live-build-tree.sh` → `noauto` | **fixed** |
| Harte Reinigung: `rm -rf .build chroot cache binary local` | **done** (User-Owner, ohne sudo) |
| `sudo lb clean --purge` | **nicht aus Agent** (sudo Passwort) |
| Bundle + Tree neu validiert | **Exit 0** |

---

## Pre-Build (Retry)

| Feld | Wert |
|------|------|
| Runtime-Gate | Exit **0** |
| auto/config noauto | **pass** — `./auto/config` Exit 0 |
| auto/build blockiert | **pass** — Exit 20 |
| Temp-Bundle Validator | Exit **0** |
| Temp-Bundle files_count | 2775 |
| Temp-Bundle source_head | `83ec644` |
| Build-Tree Validator | Exit **0** |
| Clean-Build State | **ja** — chroot/cache/binary/local/.build entfernt |
| usb_write_allowed | **false** |
| dd_executed | **false** |

---

## Dateisystem / Rechte (Phase 3)

| Feld | Wert |
|------|------|
| Pfad | `/home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live` |
| Typ | **ext4** (geeignet) |
| Freier Platz | ~1,3 TB (26 % belegt) |
| Mount | `rw,relatime` |
| Build-Dir | `gabriel:workspace`, `drwxrwsr-x` |
| umask | 0002 |

**Nicht** auf exFAT/VFAT/NTFS.

---

## Build-Versuch (Retry, Agent)

| Befehl | Ergebnis |
|--------|----------|
| `./auto/config` | **pass** (Exit 0) |
| `sudo lb build noauto` | **nicht ausgeführt** — Agent ohne sudo-Passwort |

**ISO:** keine — Build muss im Operator-Terminal fortgesetzt werden.

---

## Historische Versuche (Session 1)

| # | Problem |
|---|---------|
| 1 | `auto/config` ohne `noauto` → Rekursion |
| 2 | `lb build` → blockiertes `auto/build` |
| 3–4 | root/sudo ohne TTY |
| 5 | fakeroot → partielle chroot → **tar File exists** bei sudo-Retry |

---

## Safety-Scan (Bundle im Tree)

| Prüfung | Ergebnis |
|---------|----------|
| CDN | **pass** |
| Secrets | **pass** |
| ISO | **nicht vorhanden** |

---

## USB-Write

| Feld | Wert |
|------|------|
| usb_write_allowed | **false** |
| dd_executed | **false** |
| mkfs_executed | **false** |
| parted_write_executed | **false** |
| usb_target_device | **null** |

---

## Operator — Nächster Build (nach Clean-State)

```bash
cd /home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live
./auto/config
sudo lb build noauto 2>&1 | tee /tmp/setuphelfer-lb-build-clean.log
echo "LB_EXIT=${PIPESTATUS[0]}"
find . -maxdepth 3 -name '*.iso' -print
```

Bei erneutem tar-Fehler **zuerst** erneut `sudo lb clean --purge` und `sudo rm -rf .build chroot cache binary local`.

---

## Status

| Bereich | Status |
|---------|--------|
| Controlled ISO Build | **review_required** (Clean + noauto fix; ISO ausstehend) |
| Rescue ISO artifact | **blocked** |
| USB Write | **blocked** |
| Live Boot | **pending** |
| real_usb_write_allowed | **false** |
