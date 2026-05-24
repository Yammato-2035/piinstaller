# Rescue Stick — Live-OS Network Validation Runbook

**Version:** 1.0
**Phase:** Hardware-/Live-Test (nach Emulation-Gate `ready`, vor ISO-Build)
**Plan:** `docs/evidence/rescue/RESCUE_STICK_LIVE_OS_NETWORK_VALIDATION_PLAN.md`

## Voraussetzungen

- Runtime-Gate Exit 0 (`./scripts/check-runtime-deploy-gate.sh`)
- Build-Emulation Final-Gate `ready` mit `live_os_network_test_pending: true`
- `real_iso_build_allowed: false` (kein ISO in diesem Auftrag)
- Debian-Live- oder Rettungsstick-Umgebung mit **systemd-networkd** als Phase-1-Stack (kein NetworkManager als Default)
- Operator mit dokumentiertem Evidence-Pfad unter `docs/evidence/rescue/`

## Benötigte Hardware

- Zielrechner oder isolierte Testmaschine (kein Produktivsystem ohne Freigabe)
- Ethernet oder WLAN-Interface (optional für DHCP-Test)
- USB-Stick oder Live-Medium **nur lesend** verwenden, bis Write-Gates explizit freigegeben sind

## Erlaubte Kommandos (read-only / Status)

| Kommando | Zweck |
|----------|--------|
| `ip addr` | Interface- und Adressübersicht |
| `networkctl status` | systemd-networkd Zustand |
| `systemctl status systemd-networkd` | Dienst aktiv? |
| `curl -s http://127.0.0.1:8000/api/version` | Backend localhost |
| `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3001/` | UI localhost |
| `journalctl -u systemd-networkd -u setuphelfer-backend -u setuphelfer --no-pager -n 50` | Logs (read-only Auszug) |
| `lsblk` | Blockgeräte (read-only) |
| `ss -tlnp` | Lauschende Ports (LAN-Bind prüfen) |

## Verbotene Kommandos / Aktionen

- `apt install` / `apt upgrade` / `dpkg`
- `mount` / `umount` (für Stick-Provisioning)
- `dd`, `mkfs`, `parted` mit Schreibaktion
- `lb build`, debootstrap, chroot
- Backup, Restore, Verify Deep, Queue-Apply
- `qemu` Boot als Produktivnachweis
- ISO-Build (xorriso, grub-mkrescue)
- Automatische Reparatur/Partition/Restore über UI oder API

## Manuelle Prüfschritte

1. **Phase 0:** Runtime-Gate und Emulation-Handoff `ready` verifizieren.
2. **Ohne Kabel/WLAN:** Loopback + localhost-URLs (8000/3001) prüfen; UI ohne Internet nutzbar?
3. **Mit Netzwerk:** DHCP via systemd-networkd; `networkctl status` dokumentieren.
4. **LAN-Bind:** `ss -tlnp` — Backend/UI nur `127.0.0.1`, nicht `0.0.0.0` / LAN ohne Gate.
5. **Schreibschutz:** Keine ungefragten Write-APIs; `write_allowed=false` in relevanten Previews.
6. **CDN:** Keine Requests zu `fonts.googleapis.com` beim UI-Start (Browser-DevTools oder Proxy-Log).
7. **Evidence:** Ergebnis in `docs/evidence/rescue/` festhalten (Pass/Fail pro Zeile der Matrix).

## Erwartete Evidence

- `docs/evidence/rescue/RESCUE_STICK_LIVE_OS_NETWORK_VALIDATION_RESULT.md` (nach Test anlegen)
- Screenshots oder JSON-Auszüge: `curl` localhost, `networkctl status`, `ss -tlnp`
- Verweis auf Commit/Deploy-Stand (`bdd9865` oder später)

## Abbruchkriterien

- Backend oder UI bindet auf LAN ohne Freigabe
- Automatischer Restore/Partition/Write beim Start
- UI funktioniert nur mit Internet/CDN
- Netzwerkdienst crasht oder blockiert localhost
- Jede verbotene Aktion wäre nötig, um fortzufahren → **STOP**, ISO-Build nicht freigeben

## Pass/Fail-Matrix

| # | Prüfpunkt | Pass | Fail |
|---|-----------|------|------|
| 1 | DHCP (systemd-networkd) wenn Netz vorhanden | Lease, Route ok | Kein DHCP / Dienst down |
| 2 | Loopback aktiv | `lo` up | `lo` down |
| 3 | Backend `127.0.0.1:8000` | HTTP 200 `/api/version` | Nicht erreichbar |
| 4 | UI `127.0.0.1:3001` | HTTP 2xx/3xx | Nicht erreichbar |
| 5 | Kein LAN-Bind Default | Nur 127.0.0.1 in `ss` | `0.0.0.0` / LAN ohne Gate |
| 6 | Keine Schreibaktionen über Netz | Kein Write ohne Gate | Ungewollter Write |
| 7 | Keine Telemetrie | Kein Telemetrie-Traffic | Telemetrie aktiv |
| 8 | Kein Cloud-Zwang | Offline-Start ok | Cloud-Pflicht |
| 9 | DNS nur bei Netz | Optional ok | Hard-Fail offline |
| 10 | Offline-Betrieb | UI+API ohne WAN | Abhängigkeit von WAN |

**Gesamt:** Alle Pflichtzeilen (1–5, 8, 10) **Pass** → Live-OS Network Validation **green** → ISO-Build-Gate separat prüfbar. Mindestens ein **Fail** → `live_os_network_test_pending` bleibt, ISO blockiert.

## Nach dem Test

- `live_os_network_test_pending` in Handoff/Runner nur auf `false` setzen, wenn Evidence **green** und Operator freigibt
- ISO-Build bleibt separater Auftrag mit erneutem Phase-0-Gate
