# Controlled Command Allowlist (DE)

Der Runner akzeptiert ausschließlich allowlist-basierte `command_id`-Einträge. Kein freier Command-String.

## Pflicht-IDs (Design)

- `git_status_short`
- `git_branch`
- `git_head_short`
- `git_last_commit`
- `runtime_gate`
- `api_version_readonly`
- `dev_dashboard_status_readonly`
- `dev_dashboard_roadmap_readonly`
- `validate_roadmap_json`
- `frontend_build`
- `frontend_vitest`
- `backend_dev_dashboard_tests`
- `rescue_scripts_bash_n`
- `rescue_build_log_tail`
- `rescue_summary_json_validate`
- `build_tree_findmnt_readonly`
- `toolchain_isohybrid_check`
- `toolchain_rsvg_check`

## Operator-Handoff-IDs (nicht direkt ausführbar)

- `deploy_helper_operator_handoff`
- `rescue_iso_operator_build_handoff`
- `rescue_chroot_cleanup_handoff`

## Sicherheitsregeln

- `argv` fix, kein Shell-Parsing als Default
- `shell=false` als Standard
- Timeout je Command
- stdout/stderr getrennt speichern
- `forbidden` nie ausführen
