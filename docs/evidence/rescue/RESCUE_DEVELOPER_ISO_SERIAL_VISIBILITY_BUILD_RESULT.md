# Developer Rescue ISO — Serial Visibility Build Result

**Stand:** 2026-06-01 (Post-Build-Validierung)
**HEAD:** `dc87352`
**Profil:** `developer-qemu`  
**Run-ID:** `rescue_developer_iso_20260601_serial_visibility`  
**Repository:** PUBLIC (`Yammato-2035/piinstaller`) — **Push blocked**

## Zusammenfassung

| Phase | Ergebnis |
|-------|----------|
| Controlled ISO Build | **OK** — `LB_EXIT=0`, `status=success` |
| ISO neu gebaut | **yes** — SHA256 geändert |
| Statische Serial-Validierung | **grün** (Cmdline); Marker im ISO **gelb** (Squashfs) |
| QEMU-Smoke-Retry | **`ready_for_qemu_serial_smoke`** |

## Build-Summary

| Feld | Wert |
|------|------|
| Gestartet | 2026-06-01T17:25:11+02:00 |
| Beendet | 2026-06-01T17:28:50+02:00 |
| `exit_code` / LB_EXIT | **0** |
| `status` | **success** |
| `error_code` | null |
| `rescue_build_profile` | **developer-qemu** |
| `execution_mode` | `manual_operator_terminal` |
| `build_started` | true |

## ISO-Artefakt

| Feld | Wert |
|------|------|
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| Größe | 511705088 B (~488 MiB) |
| mtime | 2026-06-01 17:28:49 |
| **Neue SHA256** | `be016f2adacfc9906b4b92ca8ab0d6b0390ad1e39a1e2cbb1f0a98eb35241a3f` |
| **Alte SHA256** | `6a44d1fe771299305408f9e74e7b0fa3a2e7f108a7bffb415f5f4f7f46d8baae` |
| SHA geändert | **yes** |

## Live-Build-Tree (developer-qemu)

`auto/config` / `binary/isolinux/live.cfg` Boot-Append (Auszug):

```
console=tty0 console=ttyS0,115200n8 loglevel=7 systemd.log_level=debug systemd.show_status=true ignore_loglevel printk.devkmsg=on
```

- **kein** `quiet` / `splash` im Developer-`--bootappend-live`
- Marker-Skripte: `config/includes.chroot/usr/local/sbin/setuphelfer-serial-boot-markers.sh`, `setuphelfer-qemu-smoke-autopilot.sh` (auch in `chroot/`)

## Vorheriger Blockiert-Lauf (Referenz)

Exit **30** `blocked_requires_operator_sudo_policy` (Agent-Session, 16:46) — durch Operator-Build 17:25–17:28 ersetzt.

## Guardrails

Kein QEMU, USB, Backup, Restore, apt, Push in diesem Auftrag.

## Nächster Schritt

QEMU Developer-Serial-Smoke mit neuem ISO (`run-qemu-developer-iso-smoke.sh` / Fleet-Session), Run-ID neu vergeben.
