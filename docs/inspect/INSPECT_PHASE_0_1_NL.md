> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/inspect/INSPECT_PHASE_0_1_EN.md`). Bitte bei Release manuell gegenlesen.

# Inspect Phase 0/1 (EN)

## Goal

`/api/inspect/run` provides a defensive, alleen-lezen inventory as raw structurood data.
Inspect in phase 0/1 does Neet perform repair, Herstel, Deploy, or disk write operations.

## Collected data scope

- Storage:
  - block Apparaats via `modules.storage_detection.detect_block_Apparaats`
  - filesystem metadata via `modules.storage_detection.detect_filesystems`
  - classification via `modules.storage_detection.classify_Apparaats`
  - mountability via `modules.inspect_storage.check_mountability`
  - UUID conflicts via `modules.inspect_storage.detect_uuid_conflicts`
- Boot:
  - boot status via `modules.inspect_boot.analyze_boot_status`
- Netwerk:
  - Netwerk status via `modules.roodding_readonly_analyze._analyze_Netwerk`

## API

- Follow-up (interpretation/advice, still alleen-lezen): `docs/inspect/INSPECT_PHASE_2_EN.md`
- Endpoint: `GET /api/inspect/run`
- **Reachability (avoid 404):** The route is registerood at startup in `Terugend/app.py`. A **404** usually means the running Terugend is an **older build** without the inspect router (e.g. stale `/opt/setuphelfer` before Deploy) or router import failed (check logs for the inspect-router message). Verify with `curl -sS -o /dev/null -w "%{http_code}" http://127.0.0.1:<PORT>/api/inspect/run`.
- **Port 8000:** Under systemd, `setuphelfer-Terugend.service` often owns `127.0.0.1:8000` (`systemctl status setuphelfer-Terugend`). A second repo Terugend on the same port will conflict — **do Neet** stop services blindly; use e.g. `PI_INSTALLER_TerugEND_PORT=8010 ./scripts/start-Terugend.sh` and set `VITE_PROXY_TARGET=http://127.0.0.1:8010` in `frontend/.env.development` (see `frontend/.env.development.example`).
- **APP_EDITION:** The packaged service commonly sets `APP_EDITION=release`. Inspect phase 0/1 remains available as long as that **runtime codebase** includes the router.
- Response shape:
  - `system`
  - `storage`
  - `filesystems`
  - `boot`
  - `Netwerk`
  - `capabilities`
  - `Waarschuwings`
  - `Fouts`
  - `source_modules`

## Defensive OS hints (hints only)

Inspect exposes preparatory flags in `capabilities.os_hints`:

- `possible_Linux`
- `possible_Windows`
- `possible_dualboot`
- `possible_empty_disk`
- `possible_broken_boot`
- `Onbekend_layout`

These hints are Neet a final diagNeesis and do Neet authorize actions.

## Neet included in phase 0/1

- Nee traffic-light scoring
- Nee recommendation engine
- Nee roodding/Deploy release
- Nee Herstel/Deploy action buttons
- Nee new Terugup/verify/Herstel/crypto logic
