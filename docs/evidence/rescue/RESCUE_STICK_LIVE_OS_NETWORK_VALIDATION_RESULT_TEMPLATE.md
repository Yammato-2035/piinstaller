# Rescue Stick — Live-OS Network Validation Result (Template)

**Operator:** Live-Medium-Test gemäß  
`docs/runbooks/RESCUE_STICK_TEMP_RUNTIME_ON_LIVE_MEDIUM_RUNBOOK.md` und  
`docs/runbooks/RESCUE_TEMP_RUNTIME_COPY_TO_LIVE_MEDIUM.md`

## Metadaten

| Feld | Wert |
|------|------|
| Testdatum | |
| Git HEAD (Dev-Repo) | |
| bundle_manifest_sha256 | |
| bundle_validation_status | ok / fail |
| copied_to_medium_by_operator | true / false |
| Testmedium | |
| Live-System / Kernel | |
| Bootmodus (UEFI/Legacy) | |
| Hardware | |
| Netzwerkart (LAN/WLAN/keins) | |
| Internet (vorhanden/blockiert/offline getestet) | |
| Temp-Runtime-Pfad | |
| systemd-networkd | |
| NetworkManager | |
| live_boot_detected | true / false |
| setuphelfer_services_started_from_temp_bundle | true / false |
| offline_mode_tested | true / false |
| final_status | green / review_required / blocked |

## Live-Boot-Evidence

| Feld | Wert |
|------|------|
| `/proc/cmdline` | |
| `/lib/live/mount/medium` vorhanden? | |
| rootfs overlay/live? | |
| check-localonly summary | |
| ss -ltnp summary | |

## Pass/Fail-Matrix

| Prüffeld | Ergebnis | Evidence | Bewertung |
|----------|----------|----------|-----------|
| Testmedium gebootet (echtes Live) | | | pass / fail / not_tested |
| Live-System | | `uname -a` | |
| Netzwerkstack | | `networkctl`, systemctl | |
| DHCP | | `ip addr`, journal | |
| Backend localhost | | `curl 127.0.0.1:8000/api/version` | |
| UI localhost | | `curl -I 127.0.0.1:3001` | |
| LAN-Bind | | `ss -ltnp` | |
| Offline/CDN | | grep index.html, Offline-Test | |
| Auto-Write / Restore / Partition | | Service-Start, Logs | |
| Telemetrie / Cloud-Zwang | | | |
| Evidence vollständig | | Diese Datei committed | |

## Prüfpunkte 1–10

| # | Punkt | Status (pass/review_required/fail/not_tested) | Notiz |
|---|-------|-----------------------------------------------|-------|
| 1 | systemd-networkd aktiv | | |
| 2 | NetworkManager nicht erforderlich | | |
| 3 | DHCP | | |
| 4 | Loopback aktiv | | |
| 5 | DNS optional | | |
| 6 | Betrieb ohne Internet | | |
| 7 | Backend localhost | | |
| 8 | UI localhost | | |
| 9 | Keine CDN-Pflicht | | |
| 10 | Keine Telemetrie/Cloud-Zwang | | |

## Gesamtstatus

- [ ] **green** — Live-Medium + local_only + keine CDN/Auto-Write
- [ ] **review_required** — Teilpunkte offen
- [ ] **blocked** — kritische Failures

**real_iso_build_allowed:** `false` (bis expliziter ISO-Auftrag)  
**live_os_network_test:** `passed` nur bei **green** und Operator-Freigabe

## Verbotene Aktionen (bestätigen)

- [ ] Kein ISO-Build, apt, mount, dd, restore, backup, partition write in dieser Session
