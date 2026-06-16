# Workspace vs Runtime Drift

| Datei | Workspace vorhanden | /opt vorhanden | identisch | Hinweis |
|---|---:|---:|---:|---|
| backend/app.py | yes | yes | no | deploy_drift |
| backend/core/fleet_session_state.py | yes | yes | no | deploy_drift |
| backend/fleet/schemas.py | yes | yes | no | deploy_drift |
| backend/core/install_profile.py | yes | yes | no | deploy_drift |
| backend/rescue_agent/discovery.py | yes | no | n/a | workspace_only |
| backend/rescue_agent/registration.py | yes | no | n/a | workspace_only |
| backend/rescue_agent/crypto_envelope.py | yes | no | n/a | workspace_only |
| backend/rescue_agent/nftables_policy.py | yes | no | n/a | workspace_only |
| backend/rescue_agent/system_report.py | yes | no | n/a | workspace_only |
| backend/rescue_agent/routers.py | yes | no | n/a | workspace_only |
| scripts/rescue-live/fleet-session-api.sh | yes | yes | no | deploy_drift |
