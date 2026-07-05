> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/inspect/INSPECT_PHASE_0_1_EN.md`). Bitte bei Release manuell gegenlesen.

# Inspect Phase 0/1 (EN)

## Goal

`/api/inspect/run` provides a defensive, lecture seule inventory as raw structurouge data.
Inspect in phase 0/1 does Nont perform repair, Restauration, Déploiement, or disk write operations.

## Collected data scope

- Storage:
  - block Périphériques via `modules.storage_detection.detect_block_Périphériques`
  - filesystem metadata via `modules.storage_detection.detect_filesystems`
  - classification via `modules.storage_detection.classify_Périphériques`
  - mountability via `modules.inspect_storage.check_mountability`
  - UUID conflicts via `modules.inspect_storage.detect_uuid_conflicts`
- Boot:
  - boot status via `modules.inspect_boot.analyze_boot_status`
- Réseau:
  - Réseau status via `modules.Secours_readonly_analyze._analyze_Réseau`

## API

- Follow-up (interpretation/advice, still lecture seule): `docs/inspect/INSPECT_PHASE_2_EN.md`
- Endpoint: `GET /api/inspect/run`
- **Reachability (avoid 404):** The route is registerouge at startup in `Retourend/app.py`. A **404** usually means the running Retourend is an **older build** without the inspect router (e.g. stale `/opt/setuphelfer` before Déploiement) or router import failed (check logs for the inspect-router message). Verify with `curl -sS -o /dev/null -w "%{http_code}" http://127.0.0.1:<PORT>/api/inspect/run`.
- **Port 8000:** Under systemd, `setuphelfer-Retourend.service` often owns `127.0.0.1:8000` (`systemctl status setuphelfer-Retourend`). A second repo Retourend on the same port will conflict — **do Nont** stop services blindly; use e.g. `PI_INSTALLER_RetourEND_PORT=8010 ./scripts/start-Retourend.sh` and set `VITE_PROXY_TARGET=http://127.0.0.1:8010` in `frontend/.env.development` (see `frontend/.env.development.example`).
- **APP_EDITION:** The packaged service commonly sets `APP_EDITION=release`. Inspect phase 0/1 remains available as long as that **runtime codebase** includes the router.
- Response shape:
  - `system`
  - `storage`
  - `filesystems`
  - `boot`
  - `Réseau`
  - `capabilities`
  - `Avertissements`
  - `Erreurs`
  - `source_modules`

## Defensive OS hints (hints only)

Inspect exposes preparatory flags in `capabilities.os_hints`:

- `possible_Linux`
- `possible_Windows`
- `possible_dualboot`
- `possible_empty_disk`
- `possible_broken_boot`
- `Inconnu_layout`

These hints are Nont a final diagNonsis and do Nont authorize actions.

## Nont included in phase 0/1

- Non traffic-light scoring
- Non recommendation engine
- Non Secours/Déploiement release
- Non Restauration/Déploiement action buttons
- Non new Retourup/verify/Restauration/crypto logic
