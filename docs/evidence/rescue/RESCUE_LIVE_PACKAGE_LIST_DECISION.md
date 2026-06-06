# Rescue Live — Paketlisten-Entscheidung

**Datum:** 2026-06-06 (MSI-Firmware + non-free-firmware Archive-Areas)  
**Git HEAD:** `4f3ca39` → Fix-Commit `1.7.4.3`  
**Pfad:** `build/rescue/live-build/setuphelfer-rescue-live/config/package-lists/setuphelfer.list.chroot`

## Archive-Areas (live-build)

Debian Bookworm Firmware-Pakete liegen in **`non-free-firmware`**. Controlled Build nutzt:

```text
--archive-areas main contrib non-free-firmware
```

Ohne diese Areas schlägt `lb build` mit `E: Unable to locate package firmware-iwlwifi` fehl (`LB_EXIT=123`).

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
| firmware-iwlwifi | Intel WLAN (`iwlwifi-9000-…ucode`) **und** Intel BT SFI (`intel/ibt-17-16-1.sfi`) |
| firmware-intel-sound | Intel Sound-DSP-Firmware (nicht primäre BT-Quelle) |
| wireless-regdb | WLAN-Regulatory-Domain |
| network-manager | Rescue-WLAN-Menü (`nmcli`) |

## Firmware-Zuordnung (MSI i7)

| Datei / Symptom | Paket | Komponente |
|-----------------|-------|------------|
| `iwlwifi-9000-pu-b0-jf-b0-*.ucode` | `firmware-iwlwifi` | `non-free-firmware` |
| `intel/ibt-17-16-1.sfi` | **`firmware-iwlwifi`** | `non-free-firmware` |
| Intel Sound-DSP | `firmware-intel-sound` | `non-free-firmware` |

**Korrektur:** Intel-Bluetooth-Dateien wie `intel/ibt-17-16-1.sfi` werden über **`firmware-iwlwifi`** bereitgestellt, nicht über `firmware-intel-sound`.

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
- **WLAN:** `network-manager` + `firmware-iwlwifi` + `wireless-regdb` (MSI-Hardware-Pfad; kein apt zur Laufzeit)

## Setuphelfer-Dienste

- Backend: `127.0.0.1:8000` (local-only Script)
- UI: `127.0.0.1:3001`
- `SETUPHELFER_DISABLE_WRITES=1`
- Kein Auto-Restore, Auto-Partition, Auto-Backup

## apt in diesem Auftrag

**Nicht auf dem Host ausgeführt.** Pakete werden innerhalb des freigegebenen `lb build` in chroot installiert.
