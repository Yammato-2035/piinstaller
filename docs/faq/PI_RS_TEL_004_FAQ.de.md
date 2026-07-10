# PI-RS-TEL-004 FAQ (DE)

## Warum zeigt der Stick nicht mehr auf 192.168.178.140?

Der LAN-Proxy war ein **Lab-Setup** (Developer-Laptop → lokales Backend). Produktion nutzt jetzt den **IONOS Cloud-Server** `https://telemetrie.setuphelfer.de`.

## Warum reicht eine URL-Änderung nicht?

Der alte Payload (`rescue_boot_network_telemetry`, schema v1) passt nicht zum Cloud-Vertrag `telemetry.rescue.beta.v2`. Pfade, Schema und Auth unterscheiden sich.

## Was ist der neue Default?

| Einstellung | Wert |
|-------------|------|
| Base URL | `https://telemetrie.setuphelfer.de` |
| Health | `/v1/telemetry/health` |
| Ingest | `/v1/telemetry/ingest` |
| Schema | `telemetry.rescue.beta.v2` |

## Wie aktiviere ich Legacy-LAN?

```bash
SETUPHELFER_RESCUE_TELEMETRY_PATH_STYLE=legacy
SETUPHELFER_RESCUE_TELEMETRY_BASE_URL=http://192.168.178.140:8001
```

## Wo liegen Secrets?

In **`network.env`** auf dem USB (`SETUPHELFER_RESCUE_CONFIG/`) und optional einer Secret-Datei — **nicht** im Git-Repo.

## Wann wird wirklich gesendet?

Nur wenn alle Gates passieren:

- `preview_only=true`, `production_ready=false`
- `SETUPHELFER_RESCUE_TELEMETRY_OPERATOR_CONSENT=explicit`
- Auth konfiguriert (HMAC key + secret file)
- `SETUPHELFER_RESCUE_TELEMETRY_CLOUD_SEND_ENABLED=1`

## Warum kein automatischer Cloud-Test?

Tests nutzen `external_calls=false`. Echte HTTP-Calls nur mit explizitem Flag — keine Secrets in CI.

## TLS-Fehler auf der Dev-Maschine?

`SSL alert internal error` wurde als `tls_error` klassifiziert und dokumentiert. Operator prüft Zertifikat/SNI/Reverse-Proxy (→ TEL-CLOUD-HEALTH-001).

## Wann wirkt das auf dem physischen Stick?

Erst nach **PI-RS-REPACK-001** (SquashFS-Repack). Physischer Payload bleibt **1.10.0.12** bis dahin.
