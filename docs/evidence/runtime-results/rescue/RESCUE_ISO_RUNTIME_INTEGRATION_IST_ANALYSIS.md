# Rescue ISO — IST-Analyse Runtime-Integration

## Bundle

| Punkt | Build-Tree | Aktuelle ISO (13:49) |
|-------|------------|----------------------|
| `/opt/setuphelfer-rescue` | ja (`includes.chroot`) | ja (Squashfs) |
| Backend venv / Frontend | ja | ja |

## systemd

| Punkt | Build-Tree | Aktuelle ISO |
|-------|------------|--------------|
| Unit-Dateien | ja | ja |
| `multi-user.target.wants` Symlinks | **ja** (ab prepare 15:54) | **nein** → Exit **12** |

## Login / Hostname

| Punkt | Build-Tree | VM/Operator |
|-------|------------|-------------|
| `hostname=setuphelfer-rescue` | bootappend | Hostname oft `debian` (alte ISO) |
| `username=user` | bootappend | Login **user** / **live** |
| `/etc/issue`, `/etc/motd` | user/live, root gesperrt | neu im Tree |

## Tastatur / Locale / Zeitzone (neu)

| Datei | Inhalt |
|-------|--------|
| `etc/default/keyboard` | `XKBLAYOUT="de"` |
| `etc/vconsole.conf` | `KEYMAP=de-latin1` |
| `etc/default/locale` | `LANG=de_DE.UTF-8` |
| `etc/timezone` | `Europe/Berlin` |
| bootappend | `keyboard-layouts=de locales=de_DE.UTF-8 timezone=Europe/Berlin` |

## Validator

`validate-rescue-iso-squashfs.sh`: Exit **11** Bundle, **12** systemd, **13** DE-Layout, **14** Login-Hinweis.

JSON: `rescue_iso_runtime_integration_ist_analysis_latest.json`
