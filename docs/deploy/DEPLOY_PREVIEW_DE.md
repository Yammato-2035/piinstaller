# Deploy Preview (DE)

## Ziel

Deploy Preview simuliert den geplanten Deploy-Ablauf und validiert Session/Token/Ziel/Profil/Plan-Bindung,
ohne Installation, Image-Schreiben, Partitionierung oder Formatierung.

## API

`POST /api/deploy/preview`

Eingaben:

- `deploy_session_id`
- `confirmation_token`
- `target_device`
- `selected_profile`
- `plan`
- `os_source`

## OS-Quelle in dieser Phase

- `local_image`, `official_installer`: nur Strukturvalidierung
- `remote_image`: URL/Checksum werden nur formal validiert, Download bleibt blockiert (`DEPLOY_PREVIEW_REMOTE_DOWNLOAD_BLOCKED`)

## Ausgabe

- `code`
- `preview_id`
- `target`, `profile`, `os_source`
- `simulated_steps[]`
- `safety`
- `warnings[]`, `errors[]`

Alle simulierten Schritte haben `auto_allowed=false` und `requires_confirmation=true`.
