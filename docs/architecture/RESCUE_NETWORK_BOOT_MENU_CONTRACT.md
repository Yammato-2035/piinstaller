# Rescue Network Boot Menu Contract

## Netzwerkmodi

1. Offline
2. eth0 DHCP (`nmcli` bevorzugt, sonst `dhclient` falls vorhanden)
3. eth0 statische IP (`nmcli`)
4. WLAN — SSID + Passwort (**nicht** loggen/persistieren ohne Operator-Bestätigung)
5. QEMU-Lab — `http://10.0.2.2:8001`
6. Manuelle Development-Server-URL

## Pairing

- Development-Server-URL
- Einmaliger Pairing-Code
- Optional QR (später)
- Server- und Agent-Fingerprint anzeigen
- Verbindung erst nach Bestätigung

## Sicherheitsoptionen

- Read-only diagnostics only (Default Phase 1)
- Remote logs allowed
- Remote runbooks allowed (allowlist)
- Controlled write **disabled**
- Session expires after reboot
- Emergency disconnect

## Fallback ohne Netzwerk

- USB-Logbundle (später)
- Diagnose-ID / QR
- Lokale Evidence unter `/run/setuphelfer`, `/var/log/setuphelfer`

## Stub

`scripts/rescue-live/setuphelfer-rescue-network-menu.sh` schreibt nach `/run/setuphelfer/rescue-network.env` und `rescue-remote.env`.
