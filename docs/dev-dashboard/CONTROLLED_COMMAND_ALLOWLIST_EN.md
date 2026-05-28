# Controlled Command Allowlist (EN)

The runner accepts only allowlisted `command_id` entries. No free command strings.

## Required IDs (Design)

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

## Operator handoff IDs (not directly executable)

- `deploy_helper_operator_handoff`
- `rescue_iso_operator_build_handoff`
- `rescue_chroot_cleanup_handoff`
