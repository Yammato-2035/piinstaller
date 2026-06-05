# Rescue Telemetry — WoL-Prüfung Developmentserver

**Datum:** 2026-06-05
**Track:** `RESCUE_TELEMETRY_INGEST_SEPARATE_FROM_DCC`
**Host:** Developmentserver (LAN)

## Ziel

Prüfen, ob Wake-on-LAN den Entwicklungsserver vor einem Rescue-Lauf zuverlässig erreichbar macht. WoL ist **optional**; bei Unsicherheit: Server muss vor Rescue-Run online sein.

## Ergebnisse

| Check | Befund |
|-------|--------|
| Primäres LAN-IF | `enp3s0` (ethernet, connected) |
| `ethtool enp3s0` | Link OK; Wake-on-Zeile ohne elevated Rechte nicht lesbar |
| `/sys/class/net/enp3s0/device/power/wakeup` | `disabled` |
| NetworkManager | `enp3s0` → „Kabelgebundene Verbindung 1“ |
| BIOS/UEFI WoL | nicht automatisiert prüfbar — Operator-Hinweis erforderlich |
| NM/systemd WoL-Persistenz | nicht verifiziert |

## Klassifikation

**WoL nicht sicher verfügbar** auf diesem Stand.

- Telemetrie-Ingest wird **nicht** blockiert.
- Rescue-Betrieb: Entwicklungsserver **must be online before rescue run**.
- Client: Store-and-forward Queue bis `GET /api/rescue/telemetry/health` → `enabled=true`.

## Keine Secrets

Diese Datei enthält keine Tokens, MAC-Adressen als WoL-Ziele oder Credentials.

## Referenzen

- `docs/knowledge-base/development/RESCUE_TELEMETRY_INGEST.md`
- `docs/architecture/WINDOWS_RESCUE_TELEMETRY_SERVER_CONTRACT.md`
