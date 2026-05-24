# Rescue Stick Live-OS Network Validation Plan

**Version:** 1.0
**Bezug:** Build-Emulation Final-Gate `bdd9865`, `live_os_network_test_pending: true`

## Ziel

Validieren, ob **systemd-networkd** als Phase-1-Netzwerkstack für den Rettungsstick praktisch funktioniert.

## Nicht-Ziele

- kein ISO-Build in diesem Auftrag
- kein echter Boot-Test in diesem Auftrag
- kein apt
- kein chroot
- kein mount
- kein Schreibzugriff auf Datenträger

## Zu validierende Punkte im späteren Live-Test

1. DHCP per systemd-networkd
2. Loopback aktiv
3. Backend erreichbar auf `127.0.0.1:8000`
4. UI erreichbar auf `127.0.0.1:3001`
5. kein LAN-Bind per Default
6. keine Schreibaktionen über Netzwerk
7. keine Telemetrie
8. kein Cloud-Zwang
9. DNS-Auflösung nur wenn Netzwerk vorhanden
10. Betrieb ohne Netzwerk weiterhin möglich

## Akzeptanzkriterien

- `local_only` funktioniert
- Web-UI startet ohne Internet
- keine externen Fonts/CDN
- keine automatische Reparatur
- keine automatische Partitionierung
- keine automatische Restore-Ausführung
- `write_allowed=false` bis explizites späteres Gate

## Blocker für echten ISO-Build

- Netzwerkdienst startet nicht
- UI benötigt Internet
- Backend bindet unerwartet auf LAN
- externe CDN-Pflichtabhängigkeit
- automatische Write-Aktion beim Start
- fehlende Evidence

## Referenzen

- `docs/runbooks/RESCUE_STICK_LIVE_OS_NETWORK_VALIDATION_RUNBOOK.md`
- `docs/evidence/rescue/RESCUE_STICK_READONLY_BUILD_EMULATION.md`
- `docs/architecture/RESCUE_STICK_READONLY_BUILD_GATE.md`
