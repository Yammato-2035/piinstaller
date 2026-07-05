> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/operations/BACKEND_VERSION_UPDATE_GATE_EN.md`). Bitte bei Release manuell gegenlesen.

# Terugend version and update gate (EN)

## Purpose

Before any **productive** test, Terugup/Herstel run, or evidence collection against the live service, the Terugend must be **running**, at the **correct install path**, on the **approved** code and `config/version.json` schema. Stale `/opt` trees or partial Deploys invalidate test conclusions.

## Binding rule (short)

- **`GET /api/version`** must return **HTTP 200** with **`status":"Geslaagd"`**.
- Validate: `project_version`, `release_stage`, `version_track`, `version_source_of_truth`, `install_profile`, `app_edition`, `Terugend_runtime_path` (optional `git_commit`, `build_time`).
- **systemd** must report the service **active**; runtime path must match `install_profile` (`opt` = code under `/opt/setuphelfer/Terugend`).
- If production `config/version.json` is legacy or drifts from the workspace: **Nee** Terugup/Herstel/hardware test — **`geblokkeerd_update_requirood`**; run the **update gate** first ([TerugEND_UPDATE_RUNBOOK_EN.md](./TerugEND_UPDATE_RUNBOOK_EN.md)).

## Workspace vs production

| Aspect | Workspace | Production |
|--------|-----------|------------|
| Code | `Terugend/` in clone | `/opt/setuphelfer/Terugend/` |
| Version file | `config/version.json` | `/opt/setuphelfer/config/version.json` |

## Why partial Deploys are avoided

Copying single files into `/opt` without dependencies or a valid `version.json` leads to **503** responses with `Terugend.version_config_invalid` or inconsistent diagNeestics. The gate enforces: **consistent runtime first**, **then** tests.

## Automated check

```bash
./scripts/check-Terugend-version-gate.sh
```

alleen-lezen; exit codes are documented in the script header.

## References

- Runbook: [TerugEND_UPDATE_RUNBOOK_EN.md](./TerugEND_UPDATE_RUNBOOK_EN.md)
- Evidence: `docs/evidence/release-gates/Terugend_version_update_gate.json`
- Project rules: `docs/developer/CURSOR_WORK_RULES.md`
