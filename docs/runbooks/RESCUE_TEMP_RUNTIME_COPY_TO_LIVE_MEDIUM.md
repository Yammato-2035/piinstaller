# Rescue Temp Runtime — Copy to Live Medium

**Version:** 1.0  
**Bundle:** `build/rescue/temp-runtime/setuphelfer-rescue-runtime/` (lokal erzeugen)

## Voraussetzungen

- `./scripts/rescue-live/create-temp-runtime-bundle.sh` → Validator Exit **0**
- MANIFEST sha256 notieren (Evidence)
- USB/Live-Medium **bereits** vom Dateimanager eingebunden (kein `mount` in Runbook-Befehlen)

## Kopie (Operator)

1. Bundle-Verzeichnis `setuphelfer-rescue-runtime` auf eingebundenes Medium kopieren (Dateimanager oder `cp -a` auf **bereits gemounteten** Pfad, z. B. `/media/$USER/STICK/setuphelfer-rescue-runtime`).
2. **Kein** `dd`, **keine** Partitionierung, **kein** `mount`-Befehl in diesem Auftrag.
3. Nach Kopie: MANIFEST sha256 auf Medium prüfen (`sha256sum MANIFEST.json`).

## Live-System

1. Debian/Ubuntu-Live von Testmedium booten.
2. Dokumentieren: `hostname`, `uname -a`, `/proc/cmdline`, `/lib/live/mount/medium`.
3. `export SETUPHELFER_RESCUE_ROOT=/path/to/setuphelfer-rescue-runtime`
4. Terminal 1: `./scripts/rescue-live/start-backend-localonly.sh`
5. Terminal 2: `./scripts/rescue-live/start-ui-localonly.sh`
6. `./scripts/rescue-live/check-localonly.sh`

## Evidence

Ausfüllen: `RESCUE_STICK_LIVE_OS_NETWORK_VALIDATION_RESULT.md` (Template).

## Verboten

apt, mount/umount (als Anweisung), dd, mkfs, parted write, restore, backup, ISO build, LAN-Write.

## Abbruch

Backend/UI nicht localhost, CDN-Pflicht, Auto-Write → **STOP**, Status blocked/review_required.
