# Backend update runbook (EN)

## A) Manual developer/test host path (`/opt`)

1. **Backup** files to `/tmp/setuphelfer-deploy-backup-<timestamp>/` (with operator `sudo`).
2. Record **`sha256sum`** before / workspace / after.
3. **`install`** approved files (e.g. `app.py`, `core/safe_device.py`, `core/versioning.py`, diagnostics modules, **`config/version.json`**).
4. **`sudo systemctl restart setuphelfer-backend.service`**
5. **`./scripts/check-backend-version-gate.sh`** and **`curl -i http://127.0.0.1:8000/api/version`**
6. On failure: **rollback** from `/tmp` backup, restart again, update evidence.

No user-data backup job, no `dd`/`mkfs`.

## B) Package/user path (APT)

- **`apt update`** refreshes **indexes only** — does **not** install a new Setuphelfer build.
- Install/upgrade example:  
  `sudo apt update`  
  `sudo apt install setuphelfer`  
  or  
  `sudo apt upgrade setuphelfer`

**Requires:** reproducible **`.deb`**, package name, versioning, maintainer scripts, systemd policy — see `docs/roadmap/APT_UPDATE_DELIVERY_PLAN.md`.

## C) Forbidden patterns

- No single-file copies without dependency + `version.json` checks.
- No tests on a known-stale `/opt` tree.
- No backup when the version gate is not green.
