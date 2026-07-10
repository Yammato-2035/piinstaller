# TEL-CLOUD-FIX-001 — IONOS/Plesk TLS + Reverse Proxy

**Sprint:** TEL-CLOUD-FIX-001
**Date:** 2026-07-10
**Repo HEAD at investigation:** `8f4e77ea3e9208c1a527e7aebb21674d5a023761`
**Server-side fix applied from dev workstation:** **no** (SSH `217.160.0.254:22` refused; Plesk UI not reachable from agent)

## Ausgangsfehler (TEL-CLOUD-HEALTH-001)

| Check | Result |
|-------|--------|
| DNS | OK — resolves |
| TCP 443 | OK |
| TLS | **FAIL** — alert internal error (80), no peer certificate |
| HTTP | not reached |

## Diagnose (Client-side, ohne Secrets)

### DNS-Split — wahrscheinliche Root Cause

| Host | A record | TLS with SNI `telemetrie.setuphelfer.de` |
|------|----------|-------------------------------------------|
| `telemetrie.setuphelfer.de` (live DNS) | **217.160.0.254** | **FAIL** — internal error, no cert |
| `setuphelfer.de` | **85.215.118.240** | TLS completes, cert CN=`server.windogs.de` (SNI mismatch) |
| `telemetrie` @ 85.215.118.240 (`curl --resolve`) | forced | HTTP **404** (Plesk default), no telemetry proxy |

**Interpretation:** Public DNS points the telemetry subdomain at **217.160.0.254**, which does not present a valid TLS certificate. The Plesk host (**85.215.118.240**) accepts TLS but has **no** configured vhost/certificate for `telemetrie.setuphelfer.de` and returns 404 for `/v1/telemetry/health`.

### Server access from dev workstation

| Probe | Result |
|-------|--------|
| SSH `217.160.0.254:22` | connection refused |
| TCP `217.160.0.254:443` | open |
| Plesk `8443` | timeout (likely firewalled) |

## Empfohlene Operator-Maßnahmen (Plesk/IONOS)

Reference: `docs/deploy/TELEMETRY_PLESK_REVERSE_PROXY_DE.md`

### Schritt 1 — DNS korrigieren

In IONOS DNS für `setuphelfer.de`:

```text
telemetrie.setuphelfer.de  A     → 85.215.118.240   (gleicher Plesk-Host wie setuphelfer.de)
telemetrie.setuphelfer.de  AAAA  → prüfen / ggf. Plesk-IPv6 des Webservers
```

**Entfernen oder nicht nutzen:** `217.160.0.254` für `telemetrie`, solange dort kein gültiger TLS-vHost existiert.

### Schritt 2 — Plesk Subdomain + Let's Encrypt

1. Plesk → **Websites & Domains** → `setuphelfer.de`
2. Subdomain **`telemetrie.setuphelfer.de`** anlegen
3. **SSL/TLS** → Let's Encrypt für **exakt** `telemetrie.setuphelfer.de`
4. HTTPS-Redirect aktivieren

### Schritt 3 — Reverse Proxy (nginx)

Zusätzliche nginx-Direktiven für die Subdomain:

```nginx
location /v1/telemetry/ {
    proxy_pass http://127.0.0.1:8101/v1/telemetry/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto https;
    proxy_connect_timeout 10s;
    proxy_read_timeout 30s;
    client_max_body_size 64k;
}
```

Keine API-Keys, keine Authorization-Header im Proxy.

### Schritt 4 — Telemetry-App lokal prüfen (auf dem Server)

```bash
ss -ltnp | rg '8101'
curl -sS http://127.0.0.1:8101/v1/telemetry/health
systemctl status setuphelfer-telemetry-core.service 2>/dev/null || true
```

Port **8101** nur auf `127.0.0.1`, nicht in UFW öffnen.

### Schritt 5 — Abnahme (vom Dev-Rechner)

```bash
curl -v https://telemetrie.setuphelfer.de/v1/telemetry/health
openssl s_client -connect telemetrie.setuphelfer.de:443 -servername telemetrie.setuphelfer.de </dev/null
```

Erwartung nach Fix: TLS verify ok, HTTP 200 (oder definierter Health-JSON).

## Maßnahmen in diesem Sprint (Repo)

| Maßnahme | Status |
|----------|--------|
| Plesk Subdomain angelegt | **nicht ausgeführt** — kein Server-Zugang |
| Zertifikat ausgestellt | **nicht ausgeführt** |
| Reverse Proxy konfiguriert | **nicht ausgeführt** |
| DNS geändert | **nicht ausgeführt** |
| Client-Diagnose + Runbook | **dokumentiert** |

## Ergebnis

**Classification:** `tls_error_persists`

**Sub-status:** `operator_action_required` — DNS + Plesk-Konfiguration auf IONOS-Server

## Healthcheck (live DNS, nach diesem Sprint)

| Field | Value |
|-------|-------|
| URL | `https://telemetrie.setuphelfer.de/v1/telemetry/health` |
| HTTP Status | `000` (TLS failure) |
| TLS verify | failed before HTTP |
| Response body | empty |
| Ingest tested | **no** |
| Secrets used | **no** |

## Repack Decision

**`repack_allowed_with_cloud_send_disabled`**

SquashFS-Repack (PI-RS-REPACK-001) kann v2-Payload einbetten; Cloud-Send bleibt gesperrt bis `health_ok`.

## Follow-up

1. Operator führt Schritte 1–4 auf IONOS/Plesk aus
2. **TEL-CLOUD-HEALTH-002** — erneuter Client-Healthcheck nach DNS/Plesk-Fix
3. Bei `health_ok` → **PI-RS-REPACK-001**

## Evidence

`docs/evidence/tel_cloud_fix_001_ionos_plesk_tls_reverse_proxy/`

- `before-fix-client-check.txt`
- `dns-ip-diagnosis.txt`
- `after-fix-client-check.txt` (unchanged — no server fix yet)
- `operator-runbook-summary.txt`
