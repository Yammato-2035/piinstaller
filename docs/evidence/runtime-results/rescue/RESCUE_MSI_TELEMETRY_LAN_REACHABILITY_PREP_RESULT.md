# RESCUE_MSI_TELEMETRY_LAN_REACHABILITY_PREP_RESULT

**Datum:** 2026-06-07  
**Prompt:** `RESCUE_MSI_TELEMETRY_LAN_REACHABILITY_AND_OPERATOR_HANDOFF_FIX`  
**HEAD:** `452fdc8` · **Workspace-Version:** `1.7.4.5`

## Ergebnis

**LAN-Telemetrie-Pfad für MSI vorbereitet** — bestehender QEMU-Lab-Proxy (`socat`) mit LAN-Bind dokumentiert.  
**Kein physischer MSI-Boot**, **kein Proxy-Start** in diesem Lauf (Operator-Freigabe).

## Phase 0 — Ist-Zustand

| Check | Ergebnis |
|-------|----------|
| Backend bind | **`127.0.0.1:8000`** (FastAPI) |
| LAN-IP Developer-Laptop | **`192.168.178.140`** |
| Telemetrie lokal | `http://127.0.0.1:8000/api/rescue/telemetry/health` → **ok** |
| Telemetrie LAN `:8000` | **nicht erreichbar** (kein Listener auf LAN) |
| Telemetrie LAN `:8001` | **nicht erreichbar** (Proxy nicht gestartet) |
| Port 8080 | nginx auf `0.0.0.0:8080` — **nicht** SetupHelfer-Backend |
| Dev-Server | **ok**, `local_lab` |
| DCC compact-status | Telemetrie `health_ok=true`; **Rescue-Gate in DCC stale** (alte ISO-Prefix `09b9482a…`, `target_boot_validated=true` trotz Gate JSON `false`) |

## Phase 1 — Runtime-Drift

| Feld | Wert |
|------|------|
| Workspace | `1.7.4.5` |
| Runtime API | `1.7.4.1` |
| `verify_deploy_to_opt` | **Drift** (version + sha256 mismatch) |
| Klassifikation | **`RUNTIME_DEPLOY_DRIFT_1_7_4_5_PENDING`** |
| Blockiert USB-Boot? | **Nein** — blockiert aber DCC/Gate-Anzeige bis Deploy |

## Phase 2–3 — Gewählte LAN-Lösung

**Variante A (bevorzugt):** Vorhandenes Lab-Proxy-Skript mit **LAN-IP-Bind** (nicht `0.0.0.0`).

| Feld | Wert |
|------|------|
| Skript | `scripts/rescue-live/start-qemu-lab-dev-server-proxy.sh` |
| Stop | `scripts/rescue-live/stop-qemu-lab-dev-server-proxy.sh` |
| Port | **8001** |
| Bind (MSI) | **`192.168.178.140:8001`** → `127.0.0.1:8000` |
| MSI-URL | `http://192.168.178.140:8001/api/rescue/telemetry/health` |
| Ingest | `http://192.168.178.140:8001/api/rescue/telemetry/v1/ingest` |

### Sicherheitsbewertung

- Backend bleibt auf `127.0.0.1:8000` unverändert
- Proxy lauscht nur auf **Host-LAN-IP**, nicht Internet-facing ohne Firewall
- Nur TCP-Forward, keine Secrets im Proxy-Log (socat)
- **Nach MSI-Test stoppen** — temporärer Operator-Proxy
- Kein `0.0.0.0`-Bind nötig (spezifische LAN-IP reicht; kein `OPERATOR_CONFIRM_LAN_BIND` für `192.168.178.140`)

## Phase 4 — Operator-Befehle (nicht ausgeführt)

### Proxy starten (vor MSI-Boot, Developer-Laptop)

```bash
cd /home/volker/piinstaller

export SETUPHELFER_QEMU_LAB_PROXY_BIND=192.168.178.140
export SETUPHELFER_QEMU_LAB_PROXY_PORT=8001
export SETUPHELFER_QEMU_LAB_PROXY_TARGET=127.0.0.1:8000

./scripts/rescue-live/start-qemu-lab-dev-server-proxy.sh
```

### Verifikation vom Developer-Laptop

```bash
curl -sS http://192.168.178.140:8001/api/rescue/telemetry/health | jq .
curl -sS http://127.0.0.1:8000/api/rescue/telemetry/health | jq .
```

### Im MSI Live-System (nach WLAN-Verbindung)

```bash
DEV_HOST=192.168.178.140
DEV_PORT=8001

ping -c 3 "$DEV_HOST" || true
curl -sS "http://${DEV_HOST}:${DEV_PORT}/api/rescue/telemetry/health" || true
# Ingest nur mit gültigem Token/HMAC — keine Secrets loggen
```

### Proxy stoppen (nach Test)

```bash
./scripts/rescue-live/stop-qemu-lab-dev-server-proxy.sh
```

## Korrektur missverständlicher Evidence

Commit `452fdc8` („Record MSI rescue USB boot network telemetry validation“) dokumentierte **nur Developer-Preflight**, **keinen** MSI-Boot/Telemetrie-Nachweis. Gate bleibt korrekt **false** für Boot/Netzwerk/Windows-Inspect.

## Gate (unverändert — kein Fake-Green)

```text
target_laptop_booted_from_stick: false
target_network_telemetry_validated: false
windows_inspect_executable: false
```

## Next Prompt

**`RESCUE_USB_MSI_PHYSICAL_BOOT_NETWORK_TELEMETRY_OPERATOR_INGEST`**

1. Proxy starten (oben)
2. MSI physisch booten
3. Live-Checks + Telemetrie über `:8001`
4. Ergebnisse ingestieren

## Nicht ausgeführt

dd, USB-Schreiben, ISO-Rebuild, Proxy-Start, MSI-Boot, Windows-Inspect, Deploy, Push, Host-apt.
