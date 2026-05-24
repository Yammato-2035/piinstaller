# Rescue Stick — Live-OS Network Validation Result

**Version:** 1.0
**Datum:** 2026-05-24 (ca. 20:55 UTC / 22:55 CEST)
**Git HEAD (Repo):** `174cb06` (Hardware-Test-Session)
**Runtime-Gate vor Test:** Exit 0
**Plan:** `RESCUE_STICK_LIVE_OS_NETWORK_VALIDATION_PLAN.md`
**Runbook:** `RESCUE_STICK_LIVE_OS_NETWORK_VALIDATION_RUNBOOK.md`

## Hardware Live-Medium Validation (2026-05-24, Session 2)

**Testdatum:** 2026-05-24 (ca. 20:59 UTC / 22:59 CEST)
**Runtime-Gate vor Test:** Exit 0 (`174cb06`)

### Testmedium / Verfügbarkeit

| Feld | Ergebnis |
|------|----------|
| **Freigegebenes Live-/Rescue-Testmedium gebootet** | **Nein** |
| **Erkannte Umgebung** | Persistente **Ubuntu-Desktop-Installation** auf NVMe (`ext4 /`), nicht Live-ISO |
| **Live-Indikatoren** | Kein `/lib/live/mount/medium`; Kernel cmdline: `root=UUID=… ro` auf lokaler Partition |
| **Bootmodus** | UEFI (`/boot/efi` auf `nvme0n1p1`) — **Host**, nicht Live-Stick |
| **Distribution** | Ubuntu, Kernel `6.8.0-117-generic` |
| **Vorgesehenes Ziel** | Debian-Live/Rettungsstick mit **systemd-networkd** — **nicht in dieser Session bootbar** |

### Hardware (Session-Host, nicht Live-Medium)

| Feld | Wert |
|------|------|
| **Gerät** | `volker-ROG-Strix` |
| **CPU** | 32 logical CPUs (x86_64) |
| **RAM** | ca. 30 GiB |
| **Netzwerk** | LAN `enp3s0` + WLAN `wlp4s0` (DHCP via **NetworkManager**) |
| **Internet** | vorhanden; **nicht** absichtlich getrennt (kein Live-Boot) |

### Netzwerk-Stack (Live-Ziel nicht getestet)

| Prüfung | Status | Evidence |
|---------|--------|----------|
| systemd-networkd aktiv | **not_tested** | Host: **inactive** |
| NetworkManager | **active** (Host) | Nicht Ziel-Stack für Phase-1 Rescue |
| DHCP (systemd-networkd) | **not_tested** | Kein Live-Medium |
| Loopback | **pass** | `lo` UP |
| DNS optional / Offline | **not_tested** | Kein isolierter Live-Boot |

### Setuphelfer auf Session-Host (Proxy, nicht Live-Medium)

| Prüfung | Status |
|---------|--------|
| Backend `127.0.0.1:8000` | **pass** (Host `/opt`) |
| UI `127.0.0.1:3001` | **pass** |
| Local-only Bind (Setuphelfer) | **pass** — `127.0.0.1:8000/3001` |
| CDN-frei `/opt/dist` | **pass** |
| Auto-Restore/Partition/Backup beim Start | **pass** (Proxy) — nicht beobachtet |

### Pass/Fail-Matrix (Hardware Live-Medium)

| Prüffeld | Ergebnis | Bewertung |
|----------|----------|-----------|
| Echtes Live-Medium gebootet | **fail** (nicht verfügbar) | Blocker für **green** |
| systemd-networkd auf Live-Medium | **not_tested** | — |
| DHCP auf Live-Medium | **not_tested** | — |
| Backend/UI auf Live-Medium | **not_tested** | Host-Proxy separat dokumentiert |
| Offline ohne WAN auf Live-Medium | **not_tested** | — |
| Keine CDN-Pflicht (Live) | **not_tested** | Host `/opt`: pass |
| Keine Auto-Write-Aktionen (Live) | **not_tested** | Host-Proxy: pass |

### Gesamtstatus Hardware Live-Medium: **review_required**

**Begründung:** In der Agent-/Entwicklungs-Session war **kein freigegebenes Rettungsstick-/Debian-Live-Testmedium gebootet**. Die Session lief auf dem installierten Host (`volker-ROG-Strix`). Ein erneuter Host-Proxy-Check bestätigt localhost/CDN erneut, ersetzt aber **nicht** den Hardware-Live-Test.

**Kein fake green.** `real_iso_build_allowed: false`. `live_os_network_test: not passed`.

### Operator-Aktion für green

1. Freigegebenes Live-Testmedium physisch booten (kein ISO-**Build** in diesem Auftrag).
2. Runbook `RESCUE_STICK_LIVE_OS_NETWORK_VALIDATION_RUNBOOK.md` auf **gebootetem** System ausführen.
3. Evidence in diesem Abschnitt mit echten Live-Werten ergänzen; Gesamtstatus neu bewerten.

## Testumgebung (Scope — Host-Proxy Session 1)

| Feld | Wert |
|------|------|
| **Gerät** | `volker-ROG-Strix` (x86_64, Ubuntu 6.8.0-117-generic) |
| **Bootmedium** | **Kein** Rettungsstick-/Debian-Live-Boot in dieser Session |
| **Testsystem** | **Host-Runtime-Proxy:** `/opt/setuphelfer` (install_profile `opt`), nicht gebootetes Live-OS |
| **Netzwerkart (Host)** | LAN (`enp3s0`) + WLAN (`wlp4s0`) aktiv |
| **systemd-networkd** | **inactive** (disabled) auf Host |
| **NetworkManager** | **active (running)** auf Host |
| **Setuphelfer Backend/UI** | `setuphelfer-backend.service` + `setuphelfer.service` **active** |
| **Internet (Host)** | vorhanden (DHCP via NetworkManager, nicht systemd-networkd) |
| **Test ohne Internet (Live-OS)** | **not_tested** (kein isolierter Live-Boot) |

**Wichtig:** Diese Evidence dokumentiert eine **read-only Host-Proxy-Validierung** der geplanten localhost/local_only-Konfiguration. Sie ersetzt **nicht** den DHCP-/systemd-networkd-Test auf gebootetem Rettungsstick-Live-System.

## Read-only Kommando-Auszüge (Host)

```text
hostname: volker-ROG-Strix
Backend: curl http://127.0.0.1:8000/api/version → HTTP 200, project_version 1.7.1, backend_runtime_path /opt/setuphelfer/backend
UI: curl -I http://127.0.0.1:3001/ → HTTP 200
systemd-networkd: inactive (dead)
NetworkManager: active (running)
setuphelfer-backend ExecStart: uvicorn --host 127.0.0.1 --port 8000
setuphelfer UI: serve-frontend-production.py --host 127.0.0.1 --port 3001
ss: 127.0.0.1:8000, 127.0.0.1:3001 (Setuphelfer); kein 0.0.0.0 auf 8000/3001
CDN: keine fonts.googleapis.com in /opt/setuphelfer/frontend/dist/index.html
```

`journalctl` für setuphelfer-* / systemd-networkd: in Agent-Kontext keine Einträge sichtbar (Gruppe `adm`/`systemd-journal` auf Host).

## Prüfpunkte (1–10)

| # | Prüfpunkt | Status | Anmerkung |
|---|-----------|--------|-----------|
| 1 | DHCP per systemd-networkd | **not_tested** | Host nutzt NetworkManager; kein Live-OS mit systemd-networkd gebootet |
| 2 | Loopback aktiv | **pass** | `lo` UP, 127.0.0.1/8 |
| 3 | Backend 127.0.0.1:8000 | **pass** | `/api/version` JSON OK |
| 4 | UI 127.0.0.1:3001 | **pass** | HTTP 200, HTML 765 Bytes |
| 5 | kein LAN-Bind Default (Setuphelfer) | **pass** | `ss` nur 127.0.0.1:8000/3001 für Setuphelfer |
| 6 | keine Schreibaktionen über Netzwerk | **review_required** | Host-Proxy; LAN-Write-Gates nicht auf Live-OS durchgespielt |
| 7 | keine Telemetrie | **not_tested** | Kein Live-OS-Traffic-Trace; Emulation: telemetry false |
| 8 | kein Cloud-Zwang | **pass** (Proxy) | API/UI localhost ohne Cloud-Pflicht in curl-Test |
| 9 | DNS optional, kein Startblocker | **not_tested** | Kein Offline-Live-Boot |
| 10 | Betrieb ohne Internet | **not_tested** | Kein isolierter Live-Boot ohne WAN |

## Security — Local-only (Phase 4)

| Prüfung | Ergebnis |
|---------|----------|
| Backend-Bind | **pass** — nur `127.0.0.1:8000` (systemd + `ss`) |
| UI-Bind | **pass** — nur `127.0.0.1:3001` |
| Gefährliche Write-/Apply-Endpunkte offen | **review_required** — Partition-API existiert; kein Auto-Write beim Service-Start beobachtet; Live-OS nicht getestet |
| Auto-Partition / Auto-Restore / Auto-Backup | **pass** (Proxy) — keine automatische Ausführung beim Start; Emulation/systemd-Preview: false |

## Offline / CDN (Phase 5)

| Prüfung | Status |
|---------|--------|
| UI lädt lokal (curl) | **pass** |
| Keine Google-Fonts-CDN in `/opt/…/dist` | **pass** |
| Externe CDN-Pflicht | **pass** (Proxy) |
| Analytics-Pflicht | **not_tested** (Browser) |
| Cloud für Rettungsmodus | **pass** (Proxy) |

## Pass/Fail-Matrix

| Prüffeld | Ergebnis | Evidence | Bewertung |
|----------|----------|----------|-----------|
| systemd-networkd aktiv (Live-OS) | not_tested | Host: inactive | Blocker für **green** |
| DHCP (systemd-networkd) | not_tested | — | Live-Boot ausstehend |
| Backend localhost | pass | curl `/api/version` | Host-Proxy OK |
| UI localhost | pass | curl `-I :3001` | Host-Proxy OK |
| kein LAN-Bind (Setuphelfer) | pass | `ss`, systemd units | Host-Proxy OK |
| kein Auto-Restore | pass | Service-Start, Emulation | Proxy |
| kein Auto-Partition | pass | Emulation/systemd-Preview | Proxy |
| Offline-UI (Live-OS) | not_tested | — | Live-Boot ausstehend |
| keine CDN-Pflicht | pass | grep index.html | `/opt` dist |
| Evidence vollständig | review_required | Dieses Dokument | Live-OS-Teil offen |

## Gesamtstatus: **review_required**

**Begründung:** Local-only-Bind und localhost-Erreichbarkeit von Backend/UI sind auf der **Host-Runtime** nachgewiesen; CDN-freies Frontend unter `/opt` bestätigt. **Nicht** nachgewiesen: systemd-networkd + DHCP auf gebootetem Rettungsstick-Live-System, Offline-Betrieb ohne WAN auf Live-Medium, vollständige LAN-Write-/Telemetrie-Absicherung im Live-Kontext.

**Kein fake green.** **Kein ISO-Build freigegeben** (`real_iso_build_allowed: false`).

## Nächster Schritt

1. Gebootetes Debian-Live-/Rettungsstick-Testmedium (freigegeben, **kein** ISO-Build in diesem Auftrag) mit **systemd-networkd** als Default.
2. Runbook-Schritte 2–6 auf Hardware wiederholen; DHCP + Offline-Boot dokumentieren.
3. Bei **green** auf Hardware: `live_os_network_test: passed` setzen; ISO weiterhin nur separater Auftrag.

## Verbotene Aktionen in dieser Session

Kein ISO-Build, lb build, apt, mount, dd, Restore, Backup, Partition-Write, LAN-Write, qemu-Boot.
