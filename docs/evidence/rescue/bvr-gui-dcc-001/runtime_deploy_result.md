# Runtime Deploy Result

Status: **deployed_with_warning**

- Methode: `scripts/deploy-to-opt.sh` aus clean worktree `/tmp/piinstaller-dcc001-inject`
- Commit: `4098f004`
- `/api/version`: HTTP 200, `project_version` 1.9.20.0, `backend_runtime_path` `/opt/setuphelfer/backend`
- Neue Module unter `/opt` vorhanden
- Warnung: DCC-Routen im Profil `release` blockiert (`DEVELOPER_CAPABILITY_REQUIRED`) — kein Fake-Green
- Kein manueller cp-Workaround
