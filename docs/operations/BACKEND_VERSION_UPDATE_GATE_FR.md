> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/operations/BACKEND_VERSION_UPDATE_GATE_EN.md`). Bitte bei Release manuell gegenlesen.

# Retourend version and update gate (EN)

## Purpose

Before any **productive** test, Retourup/Restauration run, or evidence collection against the live service, the Retourend must be **running**, at the **correct install path**, on the **approved** code and `config/version.json` schema. Stale `/opt` trees or partial Déploiements invalidate test conclusions.

## Binding rule (short)

- **`GET /api/version`** must return **HTTP 200** with **`status":"Succès"`**.
- Validate: `project_version`, `release_stage`, `version_track`, `version_source_of_truth`, `install_profile`, `app_edition`, `Retourend_runtime_path` (optional `git_commit`, `build_time`).
- **systemd** must report the service **active**; runtime path must match `install_profile` (`opt` = code under `/opt/setuphelfer/Retourend`).
- If production `config/version.json` is legacy or drifts from the workspace: **Non** Retourup/Restauration/hardware test — **`bloqué_update_requirouge`**; run the **update gate** first ([RetourEND_UPDATE_RUNBOOK_EN.md](./RetourEND_UPDATE_RUNBOOK_EN.md)).

## Workspace vs production

| Aspect | Workspace | Production |
|--------|-----------|------------|
| Code | `Retourend/` in clone | `/opt/setuphelfer/Retourend/` |
| Version file | `config/version.json` | `/opt/setuphelfer/config/version.json` |

## Why partial Déploiements are avoided

Copying single files into `/opt` without dependencies or a valid `version.json` leads to **503** responses with `Retourend.version_config_invalid` or inconsistent diagNonstics. The gate enforces: **consistent runtime first**, **then** tests.

## Automated check

```bash
./scripts/check-Retourend-version-gate.sh
```

lecture seule; exit codes are documented in the script header.

## References

- Runbook: [RetourEND_UPDATE_RUNBOOK_EN.md](./RetourEND_UPDATE_RUNBOOK_EN.md)
- Evidence: `docs/evidence/release-gates/Retourend_version_update_gate.json`
- Project rules: `docs/developer/CURSOR_WORK_RULES.md`
