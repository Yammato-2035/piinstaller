# Developer DCC — Lokale Capability-Konfiguration (Operator-Handoff)

**Status:** `prepared_awaiting_operator`  
**Voraussetzung:** Deploy nach `/opt` abgeschlossen (`DEVELOPER_DCC_TELEMETRY_DEPLOY_OPERATOR_HANDOFF.md`)

## Ziel

Developer-Laptop unter `install_profile=release` mit lokalem Token + `DCC_DEVELOPER_ENABLED=1` DCC freischalten, ohne Release-Rechner generell zu öffnen.

## 1. Verzeichnis + Token (kein Wert ins Repo/Evidence)

```bash
sudo mkdir -p /etc/setuphelfer
sudo chmod 700 /etc/setuphelfer

sudo sh -c 'umask 077; openssl rand -hex 32 > /etc/setuphelfer/dcc_developer.token'
sudo chown root:root /etc/setuphelfer/dcc_developer.token
sudo chmod 600 /etc/setuphelfer/dcc_developer.token
```

## 2. developer.env

Hostname anpassen (`hostname` prüfen):

```bash
hostname
```

```bash
sudo tee /etc/setuphelfer/developer.env >/dev/null <<'EOF'
DCC_DEVELOPER_ENABLED=1
DCC_DEVELOPER_TOKEN_FILE=/etc/setuphelfer/dcc_developer.token
DCC_ALLOWED_HOSTNAME=volker-ROG-Strix
RESCUE_TELEMETRY_INGEST_ENABLED=1
EOF

sudo chmod 600 /etc/setuphelfer/developer.env
sudo chown root:root /etc/setuphelfer/developer.env
```

## 3. systemd Drop-in (Backend lädt Env)

Standard-Unit lädt `developer.env` **nicht** automatisch:

```bash
sudo mkdir -p /etc/systemd/system/setuphelfer-backend.service.d

sudo tee /etc/systemd/system/setuphelfer-backend.service.d/developer-capability.conf >/dev/null <<'EOF'
[Service]
EnvironmentFile=-/etc/setuphelfer/developer.env
EOF

sudo systemctl daemon-reload
sudo systemctl restart setuphelfer-backend.service
```

## 4. Smoke (Token nicht loggen)

```bash
TOKEN="$(sudo cat /etc/setuphelfer/dcc_developer.token)"

# Ohne Token — weiter blockiert
curl -sS -o /dev/null -w 'status_no_token:%{http_code}\n' \
  http://127.0.0.1:8000/api/dev-dashboard/status

# Diagnose — immer 200
curl -sS http://127.0.0.1:8000/api/dev-dashboard/capability-status | jq .

# Mit Token — DCC frei
curl -sS -o /dev/null -w 'status_with_token:%{http_code}\n' \
  -H "X-Setuphelfer-Developer-Token: $TOKEN" \
  http://127.0.0.1:8000/api/dev-dashboard/status

# Telemetrie — unabhängig vom DCC-Token
curl -sS http://127.0.0.1:8000/api/rescue/telemetry/health | jq '{status,ingest_enabled,profile_gate_independent,last_error_code,secrets_exposed}'
```

**Erwartung:**

| Endpunkt | Ohne Token | Mit Token |
|----------|------------|-----------|
| `/api/dev-dashboard/status` | 404 `PROFILE_ROUTE_BLOCKED` oder `DEVELOPER_CAPABILITY_REQUIRED` | **200** |
| `/api/dev-dashboard/capability-status` | **200** | **200** |
| `/api/rescue/telemetry/health` | **200** | **200** |

## 5. DCC UI

- Token lokal im Browser speichern (DCC blockierte Seite → „Token speichern & erneut prüfen“) **oder** Header bei API-Calls
- Token **nie** in Screenshots/Evidence

## Verboten

- Token-Wert in Git, Logs, Evidence, DCC-Anzeige
