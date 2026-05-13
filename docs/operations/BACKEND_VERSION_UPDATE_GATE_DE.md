# Backend-Version und Update-Gate (DE)

## Zweck

Vor **jedem** produktiven Test, jedem Backup-/Restore-Lauf und jedem Check gegen den **laufenden** Dienst muss sichergestellt sein, dass das Backend **läuft**, aus dem **richtigen Installationspfad** kommt, den **freigegebenen** Code und das **aktuelle** `config/version.json`-Schema nutzt. Veraltete `/opt`-Stände oder **Teildeploys** machen Testergebnisse wertlos.

## Verbindliche Regel (Kurz)

- **`GET /api/version`** liefert **HTTP 200** und **`status":"success"`**.
- Zu prüfen: `project_version`, `release_stage`, `version_track`, `version_source_of_truth`, `install_profile`, `app_edition`, `backend_runtime_path` (optional `git_commit`, `build_time`).
- **systemd**-Dienst **aktiv**; Laufzeitpfad konsistent zu `install_profile` (`opt` = Code unter `/opt/setuphelfer/backend`).
- Weicht die produktive `config/version.json` ab oder ist **Legacy** (ohne `version_source_of_truth`): **keine** Backup-/Restore-/Hardwaretests — Status **`blocked_update_required`**; zuerst **Update-Gate** ([BACKEND_UPDATE_RUNBOOK_DE.md](./BACKEND_UPDATE_RUNBOOK_DE.md)).

## Workspace vs. Produktion

| Aspekt | Workspace | Produktiv |
|--------|-----------|-----------|
| Code | `backend/` im Klon | `/opt/setuphelfer/backend/` |
| Version | `config/version.json` | `/opt/setuphelfer/config/version.json` |

## Warum Teildeploys vermieden werden

Einzeldateien nach `/opt` ohne Abhängigkeiten oder gültige `version.json` führen zu **503** mit `backend.version_config_invalid` oder inkonsistenten Diagnosen. Das Gate erzwingt: **zuerst konsistente Laufzeit**, **dann** Tests.

## Automatisierte Prüfung

```bash
./scripts/check-backend-version-gate.sh
```

Nur lesend; Exit-Codes im Skriptkopf dokumentiert.

## Verweise

- Runbook: [BACKEND_UPDATE_RUNBOOK_DE.md](./BACKEND_UPDATE_RUNBOOK_DE.md)
- Evidence: `docs/evidence/release-gates/backend_version_update_gate.json`
- Projektregeln: `docs/developer/CURSOR_WORK_RULES.md`
