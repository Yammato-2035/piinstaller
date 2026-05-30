# Rescue Developer Agent Profile (DE)

Der **Rescue Developer Edition**-Profilordner aktiviert den Development Agent für lokales Lab-Telemetrie.

## Pfad

`build/rescue/profiles/developer/`

## Inhalt

- `manifest.json` — Profil-Metadaten
- `environment/setuphelfer-dev-agent.env` — local_lab, AUTO_UPLOAD=true
- `systemd/setuphelfer-dev-agent.service` — oneshot Agent-Start

## Public Rescue

Sendet **nicht** automatisch. Siehe `build/rescue/profiles/public/`.

## Kein ISO-Build in diesem Schritt

Profil-Dateien sind vorbereitet; ISO-Integration folgt separat.
