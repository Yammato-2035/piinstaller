# Development Control Center — Fleet-Observability Roadmap

**Status:** Architektur / Produktziel (nicht vollständig implementiert)  
**Version:** 1.7.3.0  
**Bezug:** Development Server MVP, Rescue-QEMU-Lab, Remote-Modul

## Ausgangslage (heute)

| Fähigkeit | Stand |
|-----------|--------|
| Development Server Panel | Statische **Knoten-Registry** (`/api/dev-server/nodes`), Status aus letztem Report/SSH-Check |
| Live-QEMU-Session in UI | **Nein** — QEMU ist kein eigener Knoten, bis der Gast einen **Ingest-Report** sendet |
| Ampel / „hängt das System?“ | Nur grob: `online` / `busy` / `error` / `offline` aus gespeichertem Node-JSON |
| CPU/RAM/GPU/Temperatur live | **Nein** im Dev-Server-Panel (nur in Reports/SSH-Sammlung, nicht streaming) |
| Fernstart / Wiederbeleben | **Nein** (bewusst: read-only MVP, kein Wake-on-LAN) |
| E2E + Keys + Nutzerfreigabe | Remote-Modul separat; Dev-Server: Token, kein E2E für Ingest |

**QEMU-Smoke 2026-06-01 (`qemu_rescue_developer_autopilot_20260601_060855`):**

- `status: failed`, `qemu_exit_code: 124` (Timeout 1200 s)
- `dev_server_report_new: false` — Gast hat **keinen** neuen Report geliefert
- `qemu-serial.log` **leer** (0 B) — Boot-Log auf Serial kommt mit `quiet splash` praktisch nicht an
- QEMU lief **ohne KVM** trotz `/dev/kvm` — Boot auf TCG >> 20 min möglich

Die UI zeigt weiterhin die **zwei registrierten Lab-Knoten** vom 30.05.; das ist **kein Fehler der Anzeige**, sondern fehlender neuer Gast-Report.

## Zielbild (modular, auch für Schulen)

Ein **Fleet-Observability-Layer** über alle Setuphelfer-Funktionen — nicht nur Rescue:

```
┌─────────────────────────────────────────────────────────────┐
│  Development Control Center (UI)                             │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │ Fleet Board │  │ Node Detail  │  │ Consent & Remote    │ │
│  │ (Kacheln)   │  │ Metriken/Log │  │ (Freigabe-Flows)    │ │
│  └──────┬──────┘  └──────┬───────┘  └──────────┬──────────┘ │
└─────────┼────────────────┼─────────────────────┼────────────┘
          │                │                     │
          ▼                ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│  API: /api/fleet/*  (neu, modular)                         │
│  sessions · telemetry · actions · consent · audit            │
└─────────┬───────────────────────────────┬─────────────────┘
          │                               │
          ▼                               ▼
┌──────────────────┐            ┌────────────────────────────┐
│  Host / Dev      │            │  Agent auf Zielsystem       │
│  Server Ingest   │            │  (Rescue, Lab-VM, Schule)   │
└──────────────────┘            └────────────────────────────┘
```

### Pro System (Kachel / Detail)

| Anforderung | Modul-ID (Vorschlag) | Phase |
|-------------|-------------------|-------|
| Was läuft gerade? (`current_action`, Job, Autopilot-Schritt) | `fleet.session` | 1 |
| Lebt es? (grüne pulsierende LED, Heartbeat) | `fleet.heartbeat` | 1 |
| Hängt es? (rote LED, Timeout seit letztem Heartbeat) | `fleet.health_rules` | 1 |
| Log wird erzeugt? (Stream-Link, letzte Zeilen) | `fleet.log_tail` | 2 |
| Systemtyp (QEMU, Pi, PC, Rescue-Live) | `fleet.node_kind` | 0 (teilweise) |
| CPU / RAM / GPU / Temperatur | `fleet.metrics` | 2–3 |
| Vom Server „wecken“ (WoL, systemd, QEMU-Resume) | `fleet.actions.wake` | 4+ |
| Fernstart Remote (gesichert) | `remote.session` + Consent | 3–4 |

**LED-Semantik (UI):**

- **Grün pulsierend:** Heartbeat &lt; Schwellwert (z. B. 30 s), kein `stale`-Flag
- **Gelb:** `busy`, Report/Job läuft
- **Rot:** Heartbeat ausgeblieben oder expliziter `hang`/`error` vom Agent
- **Grau:** offline / Session beendet

## Sicherheit & Freigabe (Ihre Vorgaben)

| Modus | Verhalten |
|-------|-----------|
| **Lab / Test** (`local_lab`) | Fernzugriff und Daten-Upload ohne UI-Freigabe am Ziel — nur in dokumentierten Lab-Profilen, Token, kein Internet-Standard |
| **Produktion / Schule** | Aktive **Nutzerfreigabe** mit Erklärung („Was passiert?“), zeitlich begrenzt, widerrufbar |
| **Daten-Freigabe** | Separater Consent-Schritt + Sicherheitshinweise (Redaction, was verlässt das Gerät) |
| **Transport** | E2E-Verschlüsselung + Schlüssel (bestehendes Remote-Modul erweitern; Dev-Server-Ingest zusätzlich TLS + Token/Report-Signatur) |

Implementierung als **`consent.policy`**-Plugin: gleiche API, unterschiedliche Policy pro `lab_mode` / `deployment_profile`.

## Phasenplan

### Phase 0 — MVP (erledigt)

- Dev-Server Ingest, Nodes, Summary, Panel im Control Center
- Read-only SSH-Sammlung (optional, lab)

### Phase 1 — „Live Session“ für Lab/QEMU (nächster Schritt)

**Status:** implemented (workspace) / review_required (runtime deploy)

1. **Host-seitig:** Wrapper schreibt `fleet_session` via `/api/fleet/sessions` (+ JSONL-Fallback)
2. **API:** `GET /api/fleet/sessions`, `GET /api/fleet/sessions/summary`
3. **UI:** Kachel **Lab Sessions** (Telemetry-Tab im Control Center)
4. **QEMU:** `-enable-kvm` wenn verfügbar; Serial-Profil ohne `quiet` im nächsten ISO-Build

### Phase 2 — Heartbeat & Metriken

- Agent sendet alle N Sekunden kompaktes `telemetry` (CPU%, RAM, load, optional `sensors`)
- Server berechnet `stale` / rote LED
- Panel: Sparklines, letzte Aktion

### Phase 3 — Logs & Aktionen (read-only+)

- Log-Tail über sicheren Kanal (Größenlimit, Redaction)
- Freigegebene Aktionen: „Report erneut senden“, „SSH-Check“ (bereits teilweise)

### Phase 4 — Remote & Wake (mit Consent)

- E2E-Remote-Session (Keys), UI-Freigabe am Client
- WoL / gezieltes Power-Management nur nach Policy

## Abgrenzung zum aktuellen Development-Server-Panel

Das Panel listet **registrierte Knoten** und **letzte Findings** — keine QEMU-Prozess-Überwachung. Erweiterung erfolgt **modular** (neues Fleet-Board oder Tab), ohne das read-only MVP zu verwässern.

## Referenzen

- `docs/evidence/dev-server/DEV_SERVER_MVP_IMPLEMENTATION.md`
- `docs/architecture/QEMU_HOST_DEV_SERVER_REACHABILITY_POLICY.md`
- `docs/architecture/RESCUE_DEVELOPER_QEMU_SMOKE_AUTOPILOT.md`
- `frontend/src/components/devserver/DevelopmentServerPanel.tsx`
