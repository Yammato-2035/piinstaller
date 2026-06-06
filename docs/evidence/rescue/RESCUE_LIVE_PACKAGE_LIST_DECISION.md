# Rescue Live — Paketlisten-Entscheidung

**Datum:** 2026-06-06 (MSI-Firmware-Erweiterung)
**Git HEAD:** `345187b` → Rebuild-Commit erwartet
**Pfad:** `build/rescue/live-build/setuphelfer-rescue-live/config/package-lists/setuphelfer.list.chroot`

## Aktiv (minimal, konservativ)

| Paket | Zweck |
|-------|-------|
| systemd | Init + Units |
| systemd-sysv | SysV-Kompatibilität |
| ca-certificates | TLS-Basis |
| curl | API-Smoke / Diagnose |
| jq | JSON/Manifest |
| iproute2 | `ip`, Routing |
| iputils-ping | Netzwerk-Diagnose |
| net-tools | Legacy-Netzwerk-Tools |
| util-linux | Basis-Utilities inkl. `lsblk` |
| smartmontools | SMART read-only |
| python3 | Backend-Runtime |
| python3-venv | venv im Bundle |
| python3-pip | Pip-Fallback (minimal) |
| firmware-iwlwifi | Intel WLAN (MSI i7 — iwlwifi-9000-…) |
| firmware-intel-sound | Intel BT SFI (`intel/ibt-*`) |
| wireless-regdb | WLAN-Regulatory-Domain |
| network-manager | Rescue-WLAN-Menü (`nmcli`) |

## Bewusst NICHT aktiv (optional_later)

| Paket | Grund |
|-------|-------|
| avahi-daemon | Kein mDNS-Zwang |
| nginx | UI über lokalen Python/static server |
| parted | **Kein Schreib-Gate** — Partition-Write blockiert |
| ntfs-3g | Schreib-Mount-Risiko — später mit Gate |
| testdisk | Recovery-Write — später |
| gparted | GUI-Partitionierung — blockiert |

## Netzwerk-Strategie

- **systemd-networkd** mit DHCP auf `en*` und `eth*`
- **WLAN:** `network-manager` + `firmware-iwlwifi` (MSI-Hardware-Pfad; kein apt zur Laufzeit)

## Setuphelfer-Dienste

- Backend: `127.0.0.1:8000` (local-only Script)
- UI: `127.0.0.1:3001`
- `SETUPHELFER_DISABLE_WRITES=1`
- Kein Auto-Restore, Auto-Partition, Auto-Backup

## apt in diesem Auftrag

**Nicht ausgeführt.** Pakete werden erst innerhalb eines explizit freigegebenen `lb build` in chroot installiert.
