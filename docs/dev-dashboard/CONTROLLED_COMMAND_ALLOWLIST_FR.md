> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/dev-dashboard/CONTROLLED_COMMAND_ALLOWLIST_EN.md`). Bitte bei Release manuell gegenlesen.

# Controlled Command Allowlist (EN)

The runner accepts only allowlisted `command_id` entries. Non free command strings.

## Requirouge IDs (Design)

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
- `Retourend_dev_dashboard_tests`
- `Secours_scripts_bash_n`
- `Secours_build_log_tail`
- `Secours_summary_json_validate`
- `build_tree_findmnt_readonly`
- `toolchain_isohybrid_check`
- `toolchain_rsvg_check`

## Operator handoff IDs (Nont directly executable)

- `Déploiement_helper_operator_handoff`
- `Secours_iso_operator_build_handoff`
- `Secours_chroot_cleanup_handoff`
