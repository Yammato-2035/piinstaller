# Windows Rescue Telemetry Server Contract

**Track:** `windows-laptop-rescue-inspect` / `RESCUE_TELEMETRY_INGEST_SEPARATE_FROM_DCC`
**Payload kind:** `windows_rescue_inspect`
**Privacy default:** `diagnostic_metadata` (keine Dateiinhalte)

## Scope

Rescue-Stick-Telemetrie läuft **nicht** über `/api/dev-dashboard/*` oder `/api/dev-server/*`.
Unter Release-Profil bleiben DCC-Routen `PROFILE_ROUTE_BLOCKED`; Rescue-Telemetrie ist davon **ausgenommen**.

| Pfad | Methode | Profil-Gate | Aktivierung |
|------|---------|-------------|-------------|
| `/api/rescue/telemetry/health` | GET | immer erlaubt | immer |
| `/api/rescue/telemetry/v1/ingest` | POST | immer erlaubt | `RESCUE_TELEMETRY_INGEST_ENABLED=1` |

DCC darf gespeicherte Reports **anzeigen** (read-only), ist aber **keine** Voraussetzung für Empfang.

## Activation

```bash
export RESCUE_TELEMETRY_INGEST_ENABLED=1
# optional, empfohlen in Produktion:
export RESCUE_TELEMETRY_INGEST_TOKEN='<operator-generated-secret>'
# optional:
export RESCUE_TELEMETRY_INGEST_REQUIRE_HMAC=1
export RESCUE_TELEMETRY_INGEST_STORAGE_ROOT='docs/evidence/runtime-results/rescue/telemetry-ingest'
```

Ohne `RESCUE_TELEMETRY_INGEST_ENABLED=1` antwortet Ingest mit **503** (`TELEMETRY-DISABLED-001`), nicht mit `PROFILE_ROUTE_BLOCKED`.

## Authentication (Token / HMAC / mTLS)

**TLS** ist Pflicht für Transport. Keine Secrets im Repository oder in Evidence-Dateien.

### Bearer / Header-Token (MVP)

Wenn `RESCUE_TELEMETRY_INGEST_TOKEN` gesetzt ist, ist Authentifizierung **Pflicht**:

```http
Authorization: Bearer <token>
```

Alternativ:

```http
X-Setuphelfer-Telemetry-Token: <token>
```

### HMAC (optional, empfohlen)

Wenn Token konfiguriert ist oder `RESCUE_TELEMETRY_INGEST_REQUIRE_HMAC=1`:

```http
X-Setuphelfer-Payload-Hash: <hmac_sha256_hex>
```

Berechnung: `HMAC-SHA256(token, raw_request_body_bytes)` — identischer Wert wie bei gültigem Integritäts-Header.

### mTLS (Konzept, nicht MVP-Pflicht)

Für LAN/Operator-Deployment kann der Reverse-Proxy (nginx/Caddy) Client-Zertifikate verlangen.
Der Backend-Ingest bleibt tokenbasiert; mTLS terminiert am Proxy. Dokumentation: `docs/knowledge-base/development/RESCUE_TELEMETRY_INGEST.md`.

## Ingest request

```http
POST /api/rescue/telemetry/v1/ingest
Content-Type: application/json
X-Setuphelfer-Payload-Hash: <sha256_canonical_envelope_without_hash_field>
Authorization: Bearer <token>   # wenn konfiguriert
```

Legacy-Alias `POST /api/rescue/windows-inspect` ist **deprecated** — Clients sollen `/v1/ingest` nutzen.

## Health response

```json
{
  "service": "rescue_telemetry_ingest",
  "enabled": true,
  "ingest_path": "/api/rescue/telemetry/v1/ingest",
  "health_path": "/api/rescue/telemetry/health",
  "dcc_required": false,
  "profile_route_blocked_for_dcc_only": true,
  "auth_modes": ["bearer_token", "hmac_sha256_optional"],
  "mtls_documented": true,
  "storage_ok": true,
  "queue_depth": 0,
  "warnings": [],
  "checked_at": "2026-06-05T20:00:00Z"
}
```

## Success response (ACK + Hash-Match Pflicht)

```json
{
  "status": "acknowledged",
  "ack_id": "rti-abc123",
  "received_at": "2026-06-05T20:00:01Z",
  "payload_hash_sha256": "<sha256>",
  "schema_version": "1.0.0",
  "hash_match": true
}
```

Der Client gilt nur als **grün**, wenn:

- HTTP **200**
- `status = acknowledged`
- `ack_id` gesetzt
- `hash_match = true`
- `payload_hash_sha256` entspricht dem lokal berechneten Hash (Envelope ohne Feld `payload_hash_sha256`)

## Hash rule

Server berechnet:

```
sha256(canonical_json(envelope_without_payload_hash_sha256_field))
```

Das Feld `payload_hash_sha256` im Body **muss** diesem Wert entsprechen. Optional muss `X-Setuphelfer-Payload-Hash` (wenn gesendet) ebenfalls übereinstimmen.

## Store-and-forward queue

**Server-Pfade** (keine Secrets, relativer Default im Repo):

- `{storage_root}/queue/` — Metadaten bei Schreibfehler (`TELEMETRY-QUEUE-001`, HTTP 202)
- `{storage_root}/received/` — akzeptierte Envelopes
- `{storage_root}/acks/` — ACK-Records für Audit/DCC-Anzeige

**Client-Pfade** (Rescue-Stick, Konzept):

- `/var/lib/setuphelfer-rescue/telemetry-queue/`
- `/run/setuphelfer-rescue/telemetry-queue/` (Live-Session)

Bei Netzwerkfehler: `TELEMETRY-QUEUE-001`, Status `queued_local`, Retry-Plan `operator_or_rescue_agent_resend`.

## Error codes

| Code | HTTP | Meaning |
|------|------|---------|
| `TELEMETRY-DISABLED-001` | 503 | Ingest nicht aktiviert |
| `TELEMETRY-AUTH-001` | 401 | Auth fehlt/ungültig |
| `TELEMETRY-SCHEMA-001` | 422 | Ungültiges Envelope |
| `TELEMETRY-HASH-001` | 409 | Hash-Mismatch |
| `TELEMETRY-QUEUE-001` | 202 | Server-Queue (Metadaten) |
| `TELEMETRY-QUEUE-002` | 202 | Queue-Schreibfehler |
| `TELEMETRY-PRIVACY-001` | 422 | Zu viele personenbezogene Daten |
| `TELEMETRY-CONSENT-001` | 422 | Operator-Einwilligung fehlt |
| `TELEMETRY-NETWORK-001` | — | Client: Server unreachable |
| `TELEMETRY-ACK-001` | — | Client: Response ohne gültiges ACK |

## Forbidden in telemetry channel

Dateiinhalte, Cookies, Tokens, Passwörter, private Keys, unmaskierte Seriennummern (ohne explizite Freigabe).

Backup-/Dateidaten nutzen separaten Backup/Cloud-Prozess.

Schema: `docs/evidence/windows-rescue/windows_rescue_telemetry.schema.json`

Implementierung: `backend/core/rescue_telemetry_ingest.py`, `backend/rescue_telemetry/routers.py`

Hard telemetry statuses (Client): `not_created`, `queued_local`, `sent_no_ack`, `acknowledged`, `hash_mismatch`, `failed`.

## PROFILE_ROUTE_BLOCKED

Betrifft **nur** Dev/Lab-Prefixe (`/api/dev-dashboard`, `/api/dev-server`, `/api/fleet`, …).
`/api/rescue/telemetry/*` ist explizit **nicht** blockiert (`backend/runtime_governance/route_exposure.py`).
