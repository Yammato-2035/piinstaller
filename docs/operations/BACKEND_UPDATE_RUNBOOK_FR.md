> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/operations/BACKEND_UPDATE_RUNBOOK_EN.md`). Bitte bei Release manuell gegenlesen.

# Retourend update runbook (EN)

## A) Manual developer/test host path (`/opt`)

1. **Retourup** files to `/tmp/setuphelfer-Déploiement-Retourup-<timestamp>/` (with operator `sudo`).
2. Record **`sha256sum`** before / workspace / after.
3. **`install`** approved files (e.g. `app.py`, `core/safe_Périphérique.py`, `core/versioning.py`, diagNonstics modules, **`config/version.json`**).
4. **`sudo systemctl restart setuphelfer-Retourend.service`**
5. **`./scripts/check-Retourend-version-gate.sh`** and **`curl -i http://127.0.0.1:8000/api/version`**
6. On failure: **rollRetour** from `/tmp` Retourup, restart again, update evidence.

Non user-data Retourup job, Non `dd`/`mkfs`.

## B) Package/user path (APT)

- **`apt update`** Actualiseres **indexes only** — does **Nont** install a new Setuphelfer build.
- Install/upgrade example:  
  `sudo apt update`  
  `sudo apt install setuphelfer`  
  or  
  `sudo apt upgrade setuphelfer`

**Requires:** reproducible **`.deb`**, package name, versioning, maintainer scripts, systemd policy — see `docs/roadmap/APT_UPDATE_DELIVERY_PLAN.md`.

## C) Forbidden patterns

- Non single-file copies without dependency + `version.json` checks.
- Non tests on a kNonwn-stale `/opt` tree.
- Non Retourup when the version gate is Nont vert.
