# Setuphelfer Development Server (DE)

Der **Development Server** ist ein lokaler, dev-only Dienst zur Beschleunigung der Setuphelfer-Entwicklung.

## Zweck

- Test-VMs, physische Hardware und Rettungsstick Developer Edition im Lab erfassen
- Strukturierte Systemberichte (Inventory, Boot, Storage) entgegennehmen
- Remote-Rechner im Development Cockpit anzeigen
- Read-only SSH-Diagnostik (Allowlist-Profile)
- Prompt-/Runbook-Kandidaten vorbereiten (Stub)

## Modi

| Modus | Auto-Upload | SSH |
|-------|-------------|-----|
| Public Rescue | **Nein** | Nein |
| Beta Opt-in | Nur explizit, redigiert | Nein |
| Local Lab | Ja, an lokalen Dev-Server | Read-only (optional) |

## Aktivierung (lokal)

```bash
export SETUPHELFER_DEV_SERVER_ENABLED=true
export SETUPHELFER_DEV_SERVER_MODE=local_lab
export SETUPHELFER_DEV_SERVER_TOKEN=ihr-lokales-token
# optional:
export SETUPHELFER_DEV_SERVER_ALLOW_REMOTE_SSH=true
```

Siehe `.env.example.devserver` und `docs/runbooks/DEV_SERVER_LOCAL_LAB_SETUP_DE.md`.

## Sicherheit

- Keine Schreibaktionen (Backup, Restore, Partitionierung, Reparatur) in diesem MVP
- Kein freier Shell-Text — nur Allowlist-SSH-Profile
- Public Rescue sendet **nie** automatisch Daten
- Beta-Auszüge werden redigiert

## API

Präfix: `/api/dev-server/`

- `GET /health` — Status (auch wenn disabled)
- `POST /ingest/report` — Bericht + Node (Token-Header)
- `GET /nodes`, `/reports`, `/actions`, `/summary`
- SSH: `POST /nodes/{id}/ssh/check`, `collect-inventory`, `collect-storage`, `collect-boot`

## Persistenz

`docs/evidence/runtime-results/dev-server/`
