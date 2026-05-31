# Rescue Developer ISO — QEMU Boot Smoke Result

**Date:** 2026-05-31
**HEAD Start:** e51c8a7
**Branch:** main
**Version:** 1.7.3.0
**Run-ID:** `qemu_rescue_developer_iso_20260531_104633`

## Runtime gates

| Gate | Result |
|------|--------|
| Runtime-Gate | **OK** |
| Backend-Version-Gate | **OK** |
| Dev-Server Health | enabled, local_lab, storage_ok |

## ISO

| Field | Value |
|-------|-------|
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| SHA256 | `52da3e018ccbef827f8ad9bcccb9439c59e3131c501a21313d490f92a5c04326` |
| Match erwartet | **yes** |

## QEMU

| Field | Value |
|-------|--------|
| QEMU verfügbar | **yes** (8.2.2) |
| KVM | **no** (User nicht in `kvm`-Gruppe → TCG) |
| DISPLAY | `:0` |
| Gestartet | **yes** |
| Headless serial (600s) | Exit **124**, 0 Bytes Serial |
| GTK visual (900s timeout) | Fenster geöffnet, Screenshot nach ~6 min |

### Kommando (visual, erfolgreich für Boot-Nachweis)

```bash
DISPLAY=:0 qemu-system-x86_64 -m 2048 -smp 2 \
  -cdrom build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso \
  -boot d -snapshot -no-reboot \
  -display gtk \
  -serial file:docs/evidence/runtime-results/rescue/qemu/qemu_rescue_developer_iso_20260531_104633/qemu-serial-gtk.log \
  -monitor none -usb -device usb-tablet \
  -nic user,model=virtio-net-pci
```

Kein `-hda`, kein USB-Passthrough, kein Host-Blockdevice.

## Boot-Beobachtung (QEMU-Fenster)

| Check | Ergebnis |
|-------|----------|
| Boot / Live-System | **ja** — „Setuphelfer Rescue Live“ |
| Login | **ja** — `user@localhost` (Passwort `live` laut Banner) |
| Kernel | Debian `6.1.0-49-amd64` |
| Rescue Runtime | **ja** — Banner: `Bundle: /opt/setuphelfer-rescue` |
| systemd PID 1 | **nicht verifiziert** (keine read-only Gast-Kommando-Ausgabe in Evidence) |
| Dev Agent Service | **nicht verifiziert** im Gast (Screenshot zeigt kein `systemctl`) |

Screenshot (lokal, nicht committed):
`docs/evidence/runtime-results/rescue/qemu/qemu_rescue_developer_iso_20260531_104633/qemu-window-capture.png`

## Dev Agent / Dev-Server

| Check | Ergebnis |
|-------|----------|
| Dev-Server Report neu | **nein** (2 Nodes, 2 Reports unverändert) |
| Gast `curl 127.0.0.1:8000` | **Connection refused** (im Fenster sichtbar) |
| Spool im Gast | **nicht geprüft** (keine Gast-Shell in Evidence-Lauf) |

### 127.0.0.1 Gast/Host-Hinweis

`SETUPHELFER_DEV_AGENT_SERVER_URL=http://127.0.0.1:8000` im ISO-Gast zeigt auf **den Gast selbst**, nicht auf den Host-Dev-Server. Fehlender Report ist **erwartbar** ohne Host-IP/NAT (`10.0.2.2`) oder konfigurierbare Server-URL.

## Guards

| Guard | Ergebnis |
|-------|--------|
| Profile Guard Script | exit **0** |
| Public auto_upload | **false** |

## Safety

| Check | Wert |
|-------|------|
| USB write | **false** |
| dd | **false** |
| Backup | **false** |
| Restore | **false** |
| Hardwaretest | **false** |
| apt | **false** |

## Status

**review_required**

- Boot + Login + Rescue-Runtime-Banner nachgewiesen
- Serial-Headless ohne Output (TCG, kein `console=ttyS0`)
- systemd/Dev-Agent im Gast nicht per read-only Evidence verifiziert
- Dev-Server-Ingest erwartbar fehlend wegen 127.0.0.1

## Nächster Schritt

Host-Ingest-Smoke ausgeführt — **review_required** (`RESCUE_DEVELOPER_ISO_QEMU_HOST_INGEST_RESULT.md`):

- Server-Verbindung im Gast fehlgeschlagen, Tastatur EN, kein Report
- **FIX DEV SERVER BIND / QEMU HOST PORT REACHABILITY**, dann ISO-Rebuild mit `developer-qemu`-Profil

Siehe auch: `docs/evidence/rescue/RESCUE_DEV_AGENT_QEMU_SERVER_URL_FIX.md`

## Evidence

- JSON: `docs/evidence/runtime-results/rescue/qemu/qemu_rescue_developer_iso_20260531_104633/qemu_boot_smoke_result.json`
- Plan: `docs/runbooks/RESCUE_DEVELOPER_ISO_QEMU_BOOT_PLAN_DE.md`
