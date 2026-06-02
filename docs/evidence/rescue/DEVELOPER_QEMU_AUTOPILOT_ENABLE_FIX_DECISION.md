# Developer QEMU Autopilot Enable — Fix Decision

**Datum:** 2026-06-03

## Gewählte Variante

**Statischer wants-Symlink** via `write_developer_qemu_autopilot_wants()` in `prepare-controlled-live-build-tree.sh`

Nur wenn `SETUPHELFER_RESCUE_BUILD_PROFILE=developer-qemu`.

## Zielpfad

```
config/includes.chroot/etc/systemd/system/multi-user.target.wants/setuphelfer-qemu-smoke-autopilot.service
→ ../setuphelfer-qemu-smoke-autopilot.service
```

Zusätzlich: `setuphelfer-serial-boot-markers.service` (Serial-Marker-Unit).

## Warum nicht nur Hook-Fix

Hook 090 liegt im richtigen Kontext, aber `systemctl enable` im live-build-Chroot erzeugt keinen persistenten wants-Symlink (offline systemd). Backend/Service nutzen bereits das statische Prepare-Muster — Autopilot angleichen.

## Profilgrenze

| Profil | Autopilot wants |
|--------|-----------------|
| **standard** | **nein** (unverändert defensiv) |
| **developer-qemu** | **ja** |

## Sicherheitsbewertung

- Kein Autostart im Release-/Standard-ISO
- Dev-Agent weiterhin **nicht** separat enabled (Autopilot-Unit)
- Endpoint unverändert: `http://10.0.2.2:8001` (QEMU-NAT lab-only)

## Validator

- `validate-controlled-live-build-tree.sh`: wants-Symlink bei developer-qemu
- `validate-rescue-iso-squashfs.sh`: wants bei ISO mit `console=ttyS0` in ISOLINUX
