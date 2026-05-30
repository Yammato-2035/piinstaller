# Development Server Rescue Agent — MVP Architecture

## 1. Zweck

- **Developer-Rettungsstick** sendet lokale Lab-Berichte an den Development Server
- **Öffentlicher Rettungsstick** sendet **nicht** automatisch
- **Beta-Modus** später nur mit Opt-in und Redaction
- **Local Lab** darf `raw_lab` senden

## 2. Modi

| Modus                | Auto-Upload  | Redaction       | Zielserver         | Status  |
| -------------------- | ------------ | --------------- | ------------------ | ------- |
| public_rescue        | nein         | maximal         | keiner             | default |
| beta_opt_in          | nur explizit | verpflichtend   | konfiguriert       | später  |
| local_lab            | ja           | raw_lab erlaubt | lokaler Dev Server | MVP     |
| dangerous_lab_future | nein         | intern          | lokal              | später  |

## 3. Sicherheitsregeln

- Agent default **disabled**
- Aktiv nur mit `SETUPHELFER_DEV_AGENT_ENABLED=true`
- Public Auto-Upload verboten
- Kein SSH, keine Remote-Kommandos
- Keine Schreiboperationen auf dem System
- Token nur aus Umgebung
- Upload nur an konfigurierte lokale/private URL
- Timeout und Spool bei Server-Ausfall

## 4. Datenklassen

- inventory / rescue (combined report)
- storage, boot, hardware (payload sections)
- rescue_runtime
- agent_status

## 5. Module

- `backend/devserver_agent/` — Agent (Collector, Client, Spool, CLI)
- `backend/devserver/` — Development Server (Ingest API)

## 6. Spätere Ausbaustufen

- Signed read-only runbook pull
- Adaptive rescue profiles
- Dashboard live refresh
- Beta opt-in UI
- TLS/token hardening
- Backup-gated remote actions
