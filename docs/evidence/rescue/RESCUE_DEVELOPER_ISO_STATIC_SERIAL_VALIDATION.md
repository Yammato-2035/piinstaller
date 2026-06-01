# Developer Rescue ISO — Static Serial Validation

**Stand:** 2026-06-01  
**Build-Run:** `rescue_developer_iso_20260601_serial_visibility`
**LB_EXIT:** 0
**Validierung:** statisch, **kein QEMU**

## Gesamtbewertung

| Bereich | Status |
|---------|--------|
| Build-Summary konsistent | **grün** |
| ISO SHA geändert | **grün** |
| Live-Build-Tree | **grün** |
| ISO Boot-Cmdline (`strings`) | **grün** |
| Marker in ISO `strings` | **gelb** (erwartet: in Squashfs, nicht in ISO-Strings) |
| **QEMU-Smoke-Retry** | **`ready_for_qemu_serial_smoke`** |

## Live-Build-Tree

| Kriterium | Ergebnis |
|-----------|----------|
| `console=ttyS0,115200n8` | **yes** (`auto/config`, `config/binary`, `binary/isolinux/live.cfg`) |
| `console=tty0` | **yes** |
| `loglevel=7` / `systemd.log_level=debug` / `systemd.show_status=true` / `ignore_loglevel` | **yes** |
| `quiet splash` im Developer-Boot-Append | **no** |
| `SETUPHELFER_BOOT_MARKER_START` | **yes** (`setuphelfer-serial-boot-markers.sh`) |
| `SETUPHELFER_AUTOPILOT_START` | **yes** (`setuphelfer-qemu-smoke-autopilot.sh`) |
| `SETUPHELFER_DEVSERVER_AGENT_START` | **yes** |
| `SETUPHELFER_DEVSERVER_AGENT_REPORT_ATTEMPT` | **yes** |

## ISO `binary.hybrid.iso`

| Kriterium | ISO `strings` |
|-----------|----------------|
| `console=ttyS0,115200n8` | **yes** (in `append initrd=…` Zeilen) |
| `console=tty0` | **yes** |
| loglevel / systemd debug | **yes** |
| `quiet splash` im Live-Boot-Append | **no** (kein `quiet splash` in append-Zeilen; isolierte `quiet`/`splash.png` aus ISOLINUX-Menü, nicht Developer-Live-Append) |
| Autopilot-/Agent-Marker | **unknown** (nicht in `strings`; Skripte in Tree/`chroot` nachweisbar) |

## SHA256

| | SHA256 |
|---|--------|
| Alt | `6a44d1fe771299305408f9e74e7b0fa3a2e7f108a7bffb415f5f4f7f46d8baae` |
| Neu | `be016f2adacfc9906b4b92ca8ab0d6b0390ad1e39a1e2cbb1f0a98eb35241a3f` |

## Hinweis Marker / Squashfs

Runtime-Marker werden beim Boot auf `/dev/ttyS0` geschrieben; sie müssen nicht in der ISO-String-Tabelle erscheinen. Abnahme: Tree **grün** + Boot-Cmdline im ISO **grün** → QEMU-Retry freigegeben; Serial-Inhalt erst im nächsten Smoke-Lauf verifizieren.
