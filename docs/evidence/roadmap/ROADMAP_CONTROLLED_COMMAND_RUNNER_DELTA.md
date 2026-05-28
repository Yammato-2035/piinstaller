# Roadmap Delta — Controlled Command Runner

Datum: 2026-05-28

## Neuer Bereich

- `developer-tooling / controlled-command-runs`
- Status: `yellow`
- Fortschritt: `25%`
- `internal_tooling=true`, `user_facing=false`, `release_feature=false`

## Bezug zu bestehender Vorstufe

- `TERMINAL_A_READONLY` bleibt **completed**.
- Controlled Runner baut darauf auf (weiterhin ohne freie Shell).

## Prompt-Entscheidung

- Neu verfügbar: `DEV_DASHBOARD_CONTROLLED_COMMAND_RUNS_MVP` (available)
- Aktueller technischer Blocker bleibt Rescue-Cleanup:
  - `RESCUE_ISO_CHROOT_CLEANUP_FAILURE_TRIAGE` bleibt `recommended_next`
