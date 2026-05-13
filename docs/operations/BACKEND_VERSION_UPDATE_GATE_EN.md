# Backend version and update gate (EN)

## Purpose

Before any **productive** test, backup/restore run, or evidence collection against the live service, the backend must be **running**, at the **correct install path**, on the **approved** code and `config/version.json` schema. Stale `/opt` trees or partial deploys invalidate test conclusions.

## Binding rule (short)

- **`GET /api/version`** must return **HTTP 200** with **`status":"success"`**.
- Validate: `project_version`, `release_stage`, `version_track`, `version_source_of_truth`, `install_profile`, `app_edition`, `backend_runtime_path` (optional `git_commit`, `build_time`).
- **systemd** must report the service **active**; runtime path must match `install_profile` (`opt` = code under `/opt/setuphelfer/backend`).
- If production `config/version.json` is legacy or drifts from the workspace: **no** backup/restore/hardware test — **`blocked_update_required`**; run the **update gate** first ([BACKEND_UPDATE_RUNBOOK_EN.md](./BACKEND_UPDATE_RUNBOOK_EN.md)).

## Workspace vs production

| Aspect | Workspace | Production |
|--------|-----------|------------|
| Code | `backend/` in clone | `/opt/setuphelfer/backend/` |
| Version file | `config/version.json` | `/opt/setuphelfer/config/version.json` |

## Why partial deploys are avoided

Copying single files into `/opt` without dependencies or a valid `version.json` leads to **503** responses with `backend.version_config_invalid` or inconsistent diagnostics. The gate enforces: **consistent runtime first**, **then** tests.

## Automated check

```bash
./scripts/check-backend-version-gate.sh
```

Read-only; exit codes are documented in the script header.

## References

- Runbook: [BACKEND_UPDATE_RUNBOOK_EN.md](./BACKEND_UPDATE_RUNBOOK_EN.md)
- Evidence: `docs/evidence/release-gates/backend_version_update_gate.json`
- Project rules: `docs/developer/CURSOR_WORK_RULES.md`
