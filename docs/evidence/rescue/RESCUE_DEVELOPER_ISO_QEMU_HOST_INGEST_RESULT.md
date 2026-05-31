# Rescue Developer ISO — QEMU Host Dev-Server Ingest Smoke

**Date:** 2026-05-31
**HEAD Start:** 477a83b
**HEAD Ende:** 477a83b
**Branch:** main
**Version:** 1.7.3.0
**Run-ID:** `qemu_rescue_developer_host_ingest_20260531_120711`

## Runtime gates

| Gate | Result |
|------|--------|
| Runtime-Gate | **OK** |
| Backend-Version-Gate | **OK** |
| Dev-Server Health (Host) | enabled, local_lab, storage_ok |

## ISO

| Field | Value |
|-------|-------|
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| SHA256 | `52da3e018ccbef827f8ad9bcccb9439c59e3131c501a21313d490f92a5c04326` |
| Match erwartet | **yes** |
| Build vs. URL-Fix | ISO aus Build `e51c8a7` — **ohne** `server_url.py` / `developer-qemu`-Profil im Image |

## Host Dev-Server (vor / nach)

| Feld | Vor | Nach |
|------|-----|------|
| node_count | 2 | 2 |
| reports_last_24h | 2 | 2 |
| neue Node-ID | — | **keine** |
| neue Report-ID | — | **keine** |

Nodes unverändert: `agent-smoke-node`, `local-smoke-node`.

### Host-Bind (Port 8000)

```
LISTEN 127.0.0.1:8000
```

Backend lauscht **nur** auf localhost. Keine Bind-Policy-Änderung in diesem Lauf.

## QEMU

| Field | Value |
|-------|--------|
| Gestartet | **yes** (Wrapper `--operator-confirm-qemu`) |
| PID | 9627 (beendet nach manuellem Session-Ende) |
| KVM | **no** (TCG) |
| Wrapper PID-Datei | `…/qemu_gtk_pid.txt` — **OK** (`wrapper_warning_pid_file=false`) |
| Serial-Log | 0 Bytes (kein `console=ttyS0` im Live-Kernel) |

### Kommando

```bash
scripts/rescue-live/run-qemu-developer-iso-smoke.sh \
  qemu_rescue_developer_host_ingest_20260531_120711 \
  --operator-confirm-qemu \
  --remote-vnc-local \
  --ssh-forward-local \
  --keyboard de \
  --host-dev-server-url http://10.0.2.2:8000
```

Entspricht:

```bash
qemu-system-x86_64 -m 2048 -smp 2 \
  -cdrom build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso \
  -boot d -snapshot -no-reboot \
  -serial file:docs/evidence/runtime-results/rescue/qemu/qemu_rescue_developer_host_ingest_20260531_120711/qemu-serial.log \
  -display gtk -k de -usb -device usb-tablet \
  -nic user,model=virtio-net-pci,hostfwd=tcp:127.0.0.1:2222-:22 \
  -vnc 127.0.0.1:1
```

Kein `-hda`, kein USB-Passthrough, kein Host-Blockdevice.

### Remote-Zugriff

| Kanal | Bindung | Status |
|-------|---------|--------|
| VNC | `127.0.0.1:5901` | **lokal only** |
| SSH-Forward | `127.0.0.1:2222` → Gast `:22` | optional, lokal |
| Kein `0.0.0.0` | — | **bestätigt** |

Automatisierter SSH-Gast-Probe: **Timeout** (Gast-sshd nicht verifiziert / TCG-Boot zu langsam).

## Boot / Gast (Operator-Befund)

| Check | Ergebnis |
|-------|----------|
| Boot / Live-System | **ja** (Session aktiv, Operator-Feedback) |
| Login | **ja** (`user` / `live`, konsistent mit vorherigem Smoke) |
| Rescue Runtime | **plausibel** (konsistent mit vorherigem Banner-Lauf) |
| systemd PID 1 | **nicht in Evidence** (keine Gast-Shell-Ausgabe) |
| Dev-Agent Service | **nicht in Evidence** |

## Keyboard

| Check | Ergebnis |
|-------|----------|
| QEMU `-k de` | gesetzt |
| Live `keyboard-layouts=de` in `auto/config` | im Build-Tree vorhanden |
| Chroot `/etc/default/keyboard` | `XKBLAYOUT="de"` |
| Operator-Befund | **Englisch** in der X-Session |
| `keyboard_de_observed` | **false** |

**Bewertung:** `-k de` wirkt nur auf QEMU-Tastaturübersetzung (Host→Gast-Scancodes), nicht auf die XKB-Layoutwahl der Live-Session. Live-Boot-Parameter wurden im Operator-Lauf visuell nicht als DE bestätigt.

## Agent / Host-Erreichbarkeit

| Check | Ergebnis |
|-------|----------|
| ISO-Env `SETUPHELFER_DEV_AGENT_SERVER_URL` | `http://127.0.0.1:8000` (Gast-localhost) |
| Geplante Gast-URL | `http://10.0.2.2:8000` |
| Operator: Server-Verbindung | **Failed to connect** |
| `curl 10.0.2.2:8000` (automatisiert) | **nicht ausgeführt** |
| Host-Dev-Server-Report | **nein** |
| Spool im Gast | **nicht geprüft** |

### Ursachen (priorisiert)

1. **Falsche URL im Gast:** ISO-Env und UI zeigen auf `127.0.0.1:8000` → trifft den Gast, nicht den Host.
2. **`network_bind_pending`:** Host-Backend nur `127.0.0.1:8000`. Slirp/NAT von `10.0.2.2` kann je nach Stack scheitern, wenn kein erreichbarer Host-Listener für die weitergeleitete Verbindung existiert.
3. **ISO stale:** `477a83b`-Fix (`server_url.py`, `--qemu-host-fallback`, `developer-qemu`-Profil) ist **nicht** im gebauten ISO — CLI-Flags im Gast würden fehlen oder nicht greifen.

## Safety

| Check | Wert |
|-------|------|
| USB write | **false** |
| dd | **false** |
| Backup | **false** |
| Restore | **false** |
| Hardwaretest | **false** |
| apt | **false** |
| Host-Geräte | **unverändert** |

## Status

**review_required**

- QEMU gestartet, lokale Remote-Konsolen OK, ISO-SHA OK, Gates OK
- Operator: Boot/Login OK, aber **Server-Verbindung fehlgeschlagen**, **Tastatur EN**
- Kein Host-Dev-Server-Ingest (Summary unverändert)
- Kein Erfolg ohne Report — korrekt **nicht** `success`

## Nächster Schritt

**FIX DEV SERVER BIND / QEMU HOST PORT REACHABILITY**

1. Host-Dev-Server für QEMU-Slirp erreichbar machen (z. B. dokumentierter Lab-Bind oder `hostfwd`/Proxy — ohne Safety-Gates zu schwächen).
2. Developer-ISO mit `developer-qemu`-Profil **neu bauen** (`SETUPHELFER_DEV_AGENT_SERVER_URL=http://10.0.2.2:8000`, `server_url.py` im Bundle).
3. Live-Keyboard: X-Session-Layout verifizieren (`localectl`, Autostart-Hook) und erneut smoke-testen.

## Evidence

- JSON: `docs/evidence/runtime-results/rescue/qemu/qemu_rescue_developer_host_ingest_20260531_120711/qemu_host_ingest_result.json`
- Host Summary vor/nach: `host_dev_server_summary_before.json`, `host_dev_server_summary_after.json`
- Vorheriger Boot-Smoke: `RESCUE_DEVELOPER_ISO_QEMU_BOOT_SMOKE_RESULT.md`
- URL-Fix (Code): `RESCUE_DEV_AGENT_QEMU_SERVER_URL_FIX.md`
