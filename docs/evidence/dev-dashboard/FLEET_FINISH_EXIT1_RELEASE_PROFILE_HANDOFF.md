# Fleet Finish Triage — Release-Profil Handoff

**Stand:** 2026-06-02  
**Aktuelles Profil (gemessen):** `local_lab`  
**In diesem Lauf:** kein Profilwechsel (kein sudo)

## Handoff — zurück auf release

```bash
cd /home/volker/piinstaller
sudo install -m 0644 \
  packaging/systemd/dropins/92-install-profile-release.conf.example \
  /etc/systemd/system/setuphelfer-backend.service.d/install-profile.conf
sudo systemctl daemon-reload
sudo systemctl restart setuphelfer-backend.service

./scripts/check-runtime-profile-deploy-gate.sh
curl -sS http://127.0.0.1:8000/api/version | jq '{install_profile, profile_gate_status, backend_runtime_path}'
curl -sS -i http://127.0.0.1:8000/api/dev-dashboard/status | head -5
curl -sS -i http://127.0.0.1:8000/api/fleet/sessions | head -5
```

Erwartung in `release`:

- `install_profile`: `release`
- `/api/dev-dashboard/status`: **404** `PROFILE_ROUTE_BLOCKED`
- `/api/fleet/sessions`: **404** `PROFILE_ROUTE_BLOCKED`

## Script-Fix deployen

Der Fix für `${3:-{}}` liegt im Workspace; `/opt` erst nach `deploy-to-opt` aus Worktree/Commit.
