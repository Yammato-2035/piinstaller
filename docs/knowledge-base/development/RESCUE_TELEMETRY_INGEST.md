# Rescue Telemetry Ingest (separat vom DCC)

## Überblick

Rettungsstick-Telemetrie (Windows-Inspect-Metadaten) wird über **`/api/rescue/telemetry/*`** empfangen — **nicht** über das Development Control Center (`/api/dev-dashboard/*`).

| Aspekt | DCC / Dev-Server | Rescue Telemetry Ingest |
|--------|------------------|-------------------------|
| Pfad | `/api/dev-dashboard/*`, `/api/dev-server/*` | `/api/rescue/telemetry/*` |
| Release-Profil | blockiert (`PROFILE_ROUTE_BLOCKED`) | **erlaubt** |
| Aktivierung | Install-Profil `local_lab` / `developer` | `RESCUE_TELEMETRY_INGEST_ENABLED=1` |
| DCC für Empfang nötig? | ja (Dev-Server) | **nein** |
| DCC darf anzeigen? | ja | ja (read-only aus `received/` / `acks/`) |

Vertrag: `docs/architecture/WINDOWS_RESCUE_TELEMETRY_SERVER_CONTRACT.md`

## Umgebungsvariablen

| Variable | Bedeutung |
|----------|-----------|
| `RESCUE_TELEMETRY_INGEST_ENABLED=1` | Ingest akzeptiert POST |
| `RESCUE_TELEMETRY_INGEST_TOKEN` | Shared Secret (Bearer / HMAC) |
| `RESCUE_TELEMETRY_INGEST_REQUIRE_HMAC=1` | HMAC-Header Pflicht wenn Token gesetzt |
| `RESCUE_TELEMETRY_INGEST_STORAGE_ROOT` | Speicherwurzel (Default: `docs/evidence/runtime-results/rescue/telemetry-ingest`) |

Keine Token-Werte in Evidence oder Git committen.

## Endpunkte

- `GET /api/rescue/telemetry/health` — Status, Queue-Tiefe, Warnungen
- `POST /api/rescue/telemetry/v1/ingest` — Envelope mit ACK + Hash-Match

## Authentifizierung

1. **Bearer / Header-Token** — `Authorization: Bearer …` oder `X-Setuphelfer-Telemetry-Token`
2. **HMAC** — `X-Setuphelfer-Payload-Hash: HMAC-SHA256(token, body_bytes)` (optional/empfohlen)
3. **mTLS (Konzept)** — Client-Zertifikat am Reverse-Proxy; Backend bleibt tokenbasiert

## Store-and-forward

- Client queue: `/var/lib/setuphelfer-rescue/telemetry-queue/` (Konzept)
- Server queue: `{storage_root}/queue/` bei Schreibproblemen (HTTP 202)
- Erfolg: `{storage_root}/received/` + `{storage_root}/acks/`

## Wake-on-LAN (optional)

WoL ist **kein** Blocker für Telemetrie-Ingest, sondern optionales Operator-/Netzwerkfeature zum Aufwecken eines schlafenden Entwicklungsservers.

### Prüfstand Developmentserver (2026-06-05)

| Prüfung | Interface `enp3s0` | Ergebnis |
|---------|-------------------|----------|
| `ethtool` Wake-on-Zeile | ohne root-Rechte | nicht auslesbar (`Operation not permitted`) |
| sysfs `power/wakeup` | `enp3s0` | `disabled` |
| NetworkManager | Kabelgebundene Verbindung 1 | aktiv, keine WoL-Persistenz verifiziert |
| BIOS/UEFI | — | manuell: „Wake on LAN“ / „Erweitert → ACPI“ prüfen |

**Klassifikation:** WoL auf diesem Host **nicht sicher verfügbar**. Entwicklungsserver gilt als **„must be online before rescue run“** — Rescue-Stick sendet in Queue (`TELEMETRY-QUEUE-001`) bis Server erreichbar ist.

WoL aktivieren (Operator, optional):

```bash
# BIOS: Wake on LAN aktivieren
sudo ethtool enp3s0 | grep -i wake
sudo ethtool -s enp3s0 wol g
# Persistenz (Beispiel systemd-networkd / NM) — distributionsabhängig dokumentieren
```

Evidence (ohne Secrets): `docs/evidence/dev-dashboard/RESCUE_TELEMETRY_WOL_DEVSERVER_CHECK.md`

## Abgrenzung Local Lab Telemetry

`docs/knowledge-base/development/LOCAL_LAB_TELEMETRY.md` beschreibt **Dev-Server-Ingest** (`POST /api/dev-server/ingest/report`) unter `local_lab`. Rescue-Telemetrie ist ein **paralleler Kanal** für Release-taugliche Inspect-Metadaten.
