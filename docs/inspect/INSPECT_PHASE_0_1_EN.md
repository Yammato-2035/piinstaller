# Inspect Phase 0/1 (EN)

## Goal

`/api/inspect/run` provides a defensive, read-only inventory as raw structured data.
Inspect in phase 0/1 does not perform repair, restore, deploy, or disk write operations.

## Collected data scope

- Storage:
  - block devices via `modules.storage_detection.detect_block_devices`
  - filesystem metadata via `modules.storage_detection.detect_filesystems`
  - classification via `modules.storage_detection.classify_devices`
  - mountability via `modules.inspect_storage.check_mountability`
  - UUID conflicts via `modules.inspect_storage.detect_uuid_conflicts`
- Boot:
  - boot status via `modules.inspect_boot.analyze_boot_status`
- Network:
  - network status via `modules.rescue_readonly_analyze._analyze_network`

## API

- Follow-up (interpretation/advice, still read-only): `docs/inspect/INSPECT_PHASE_2_EN.md`
- Endpoint: `GET /api/inspect/run`
- **Reachability (avoid 404):** The route is registered at startup in `backend/app.py`. A **404** usually means the running backend is an **older build** without the inspect router (e.g. stale `/opt/setuphelfer` before deploy) or router import failed (check logs for the inspect-router message). Verify with `curl -sS -o /dev/null -w "%{http_code}" http://127.0.0.1:<PORT>/api/inspect/run`.
- **Port 8000:** Under systemd, `setuphelfer-backend.service` often owns `127.0.0.1:8000` (`systemctl status setuphelfer-backend`). A second repo backend on the same port will conflict — **do not** stop services blindly; use e.g. `PI_INSTALLER_BACKEND_PORT=8010 ./scripts/start-backend.sh` and set `VITE_PROXY_TARGET=http://127.0.0.1:8010` in `frontend/.env.development` (see `frontend/.env.development.example`).
- **APP_EDITION:** The packaged service commonly sets `APP_EDITION=release`. Inspect phase 0/1 remains available as long as that **runtime codebase** includes the router.
- Response shape:
  - `system`
  - `storage`
  - `filesystems`
  - `boot`
  - `network`
  - `capabilities`
  - `warnings`
  - `errors`
  - `source_modules`

## Defensive OS hints (hints only)

Inspect exposes preparatory flags in `capabilities.os_hints`:

- `possible_linux`
- `possible_windows`
- `possible_dualboot`
- `possible_empty_disk`
- `possible_broken_boot`
- `unknown_layout`

These hints are not a final diagnosis and do not authorize actions.

## Not included in phase 0/1

- no traffic-light scoring
- no recommendation engine
- no rescue/deploy release
- no restore/deploy action buttons
- no new backup/verify/restore/crypto logic
