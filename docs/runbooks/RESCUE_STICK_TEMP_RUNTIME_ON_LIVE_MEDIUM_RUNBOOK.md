# Rescue Stick — Temp Runtime on Live Medium (Runbook)

**Version:** 1.0  
**Bezug:** `RESCUE_LIVE_TEMP_RUNTIME_PREP_IST.md`, `RESCUE_TEMP_RUNTIME_BUNDLE_PREVIEW.md`  
**Kein ISO-Build in diesem Auftrag**

## Voraussetzungen

- Freigegebenes Debian-/Ubuntu-**Live-Testmedium** gebootet (kein Persist-Install als Ersatz)
- Temp-Bundle `setuphelfer-rescue-runtime/` auf Live-System verfügbar (Operator-Kopie, ohne mount/dd in Prep-Doku)
- Runtime-Gate im Dev-Repo Exit 0 (`6adfcf6+`)
- `real_iso_build_allowed: false`

## Schritt 1 — Live-Medium booten & dokumentieren

```bash
hostname || true
uname -a || true
cat /proc/cmdline || true
```

Dokumentieren: Gerät, Bootmodus (UEFI/Legacy), Kernel, Live vs. Persist (z. B. `/lib/live/mount/medium`).

## Schritt 2 — Netzwerk-Stack erfassen (read-only)

```bash
ip addr || true
networkctl status || true
systemctl is-active systemd-networkd || true
systemctl status systemd-networkd --no-pager || true
systemctl is-active NetworkManager || true
systemctl status NetworkManager --no-pager || true
lsblk || true
```

## Schritt 3 — Temp-Runtime starten (local-only)

```bash
export SETUPHELFER_RESCUE_ROOT=/path/to/setuphelfer-rescue-runtime
cd "$SETUPHELFER_RESCUE_ROOT"
./scripts/rescue-live/start-backend-localonly.sh   # Terminal 1
./scripts/rescue-live/start-ui-localonly.sh        # Terminal 2
```

**Verboten:** sudo, apt, mount, restore, backup, partition apply, `ALLOW_REMOTE_ACCESS=true`.

## Schritt 4 — Local-only prüfen

```bash
./scripts/rescue-live/check-localonly.sh
ss -ltnp || true
```

Erwartung: nur `127.0.0.1:8000` und `127.0.0.1:3001` für Setuphelfer.

## Schritt 5 — Offline / CDN (wenn möglich)

- WAN abschalten oder Kabel trennen (nur wenn sicher ohne Live-System-Schaden)
- UI im Browser oder `curl -I http://127.0.0.1:3001/` erneut prüfen
- Keine Requests zu `fonts.googleapis.com`

Wenn Offline nicht testbar: **review_required**, nicht green.

## Schritt 6 — Auto-Write prüfen

- Kein automatischer Restore/Partition/Backup beim Start
- Optional (wenn Backend läuft): Partitions-Preview nur lesend; kein Queue-Apply

## Schritt 7 — Evidence sammeln

Ausgabe von Schritt 1–6 in  
`docs/evidence/rescue/RESCUE_STICK_LIVE_OS_NETWORK_VALIDATION_RESULT.md`  
(mit Template `RESCUE_STICK_LIVE_OS_NETWORK_VALIDATION_RESULT_TEMPLATE.md`).

Journal (read-only):

```bash
journalctl -u systemd-networkd -n 80 --no-pager || true
```

## Verbotene Kommandos

apt install/upgrade, mount/umount, dd, mkfs, parted write, restore, backup, queue apply, lb build, ISO build, chroot, debootstrap.

## Abbruchkriterien

- Backend/UI bindet auf `0.0.0.0` ohne Gate
- UI benötigt Internet/CDN
- Auto-Restore/Partition ausgelöst
- Verbotene Aktion nötig → **STOP**, Status **blocked**

## Pass/Fail-Matrix (Kurz)

| # | Prüfpunkt | Pass |
|---|-----------|------|
| 1 | Live-Medium gebootet | Ja, dokumentiert |
| 2 | systemd-networkd (Phase-1) | aktiv oder begründet |
| 3 | DHCP | funktioniert wenn Netz da |
| 4 | Backend localhost | HTTP 200 `/api/version` |
| 5 | UI localhost | HTTP 2xx |
| 6 | Kein LAN-Bind | nur 127.0.0.1 |
| 7 | Offline/CDN | UI ohne WAN, kein Google Fonts |
| 8 | Kein Auto-Write | keine Auto-Aktion |

**Green gesamt:** alle Pflichtzeilen Pass + Evidence vollständig.  
**ISO-Build:** weiterhin separater Auftrag.
