# Control Center Router Audit — E.10

## Verbleibend in app.py (18 dev-dashboard Routen)

- `GET /api/dev-dashboard/status` → facade_required
- `GET /api/dev-dashboard/rescue-build/status` → facade_required
- `GET /api/dev-dashboard/rescue-iso/status` → facade_required
- `POST /api/dev-dashboard/rescue-iso/step` → unsafe
- `GET /api/dev-dashboard/rescue-iso/step/{action_id}` → unsafe
- `POST /api/dev-dashboard/rescue-iso/operator-commands/sudo-clean` → extract_now
- `POST /api/dev-dashboard/rescue-iso/operator-commands/build` → extract_now
- `GET /api/dev-dashboard/rescue-usb/candidates` → extract_now
- `GET /api/dev-dashboard/rescue-usb/selection` → extract_now
- `POST /api/dev-dashboard/rescue-usb/selection` → extract_now
- `POST /api/dev-dashboard/notifications/test-dashboard` → unsafe
- `POST /api/dev-dashboard/notifications/test-email` → unsafe
- `GET /api/dev-dashboard/deploy/status` → unsafe
- `POST /api/dev-dashboard/deploy/request` → unsafe
- `GET /api/dev-dashboard/deploy/logs` → unsafe
- `POST /api/dev-dashboard/deploy/operator-setup-commands` → unsafe
- `POST /api/dev-dashboard/actions/restart-backend` → unsafe
- `POST /api/dev-dashboard/actions/start-backup` → unsafe

## Extrahiert nach control_center_readonly.py (7)

- `GET /api/dev-dashboard/control-center-summary`
- `GET /api/dev-dashboard/roadmap`
- `GET /api/dev-dashboard/update/status`
- `GET /api/dev-dashboard/packaging/readiness`
- `GET /api/dev-dashboard/project-overview`
- `GET /api/dev-dashboard/prompt-findings`
- `GET /api/dev-dashboard/cursor-meta-prompt`
