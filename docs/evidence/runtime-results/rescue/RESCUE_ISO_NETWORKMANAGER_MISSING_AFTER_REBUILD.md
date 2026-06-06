# RESCUE_ISO_NETWORKMANAGER_MISSING_AFTER_REBUILD

**Datum:** 2026-06-07  
**Prompt:** `RESCUE_ISO_UEFI_AND_NETWORKMANAGER_FAILURE_TRIAGE_FIX`

## Symptom (ISO `dc351387…`)

- Build-Log: `network-manager` installiert, später **`Removing network-manager`**
- SquashFS: Symlinks unter `/etc/systemd/system/…`, aber **kein** `/usr/bin/nmcli`, **kein** `NetworkManager.service`
- Validator/Smoke: `nmcli_present=false`, `network_manager_functional=false`

## Root Cause NetworkManager

**`lb_chroot_live-packages`** installiert `live-config-sysvinit`, weil live-build **ohne** `--initsystem systemd` standardmäßig SysV-Init-Live-Config nutzt.

Entfernte Pakete (Build-Log Zeile ~2540):

```
dbus-user-session libpam-systemd modemmanager network-manager polkitd systemd-sysv
```

→ `live-config-sysvinit` + SysV-Stack widerspricht `--bootappend-live init=/lib/systemd/systemd`, entfernt NM **vor** `lb_binary_rootfs` / SquashFS.

## Workspace-Fix

1. `auto/config`: **`--initsystem systemd`**
2. Paketliste: **`wpasupplicant`** ergänzt
3. Hook **`015-ensure-network-manager.hook.chroot`**: NM/wpasupplicant nach live-packages nachinstallieren falls `nmcli` fehlt
4. Service-Hook: **`NetworkManager.service`** statt `systemd-networkd`

## ISO-Rebuild

**Nein** — Wirksamkeit erst nach Operator-clean + Rebuild nachweisbar.

## Nicht ausgeführt

USB-dd, MSI-Retest, Windows-Inspect.
