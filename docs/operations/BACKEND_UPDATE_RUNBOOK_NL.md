> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/operations/BACKEND_UPDATE_RUNBOOK_EN.md`). Bitte bei Release manuell gegenlesen.

# Terugend update runbook (EN)

## A) Manual developer/test host path (`/opt`)

1. **Terugup** files to `/tmp/setuphelfer-Deploy-Terugup-<timestamp>/` (with operator `sudo`).
2. Record **`sha256sum`** before / workspace / after.
3. **`install`** approved files (e.g. `app.py`, `core/safe_Apparaat.py`, `core/versioning.py`, diagNeestics modules, **`config/version.json`**).
4. **`sudo systemctl restart setuphelfer-Terugend.service`**
5. **`./scripts/check-Terugend-version-gate.sh`** and **`curl -i http://127.0.0.1:8000/api/version`**
6. On failure: **rollTerug** from `/tmp` Terugup, restart again, update evidence.

Nee user-data Terugup job, Nee `dd`/`mkfs`.

## B) Package/user path (APT)

- **`apt update`** Vernieuwenes **indexes only** — does **Neet** install a new Setuphelfer build.
- Install/upgrade example:  
  `sudo apt update`  
  `sudo apt install setuphelfer`  
  or  
  `sudo apt upgrade setuphelfer`

**Requires:** reproducible **`.deb`**, package name, versioning, maintainer scripts, systemd policy — see `docs/roadmap/APT_UPDATE_DELIVERY_PLAN.md`.

## C) Forbidden patterns

- Nee single-file copies without dependency + `version.json` checks.
- Nee tests on a kNeewn-stale `/opt` tree.
- Nee Terugup when the version gate is Neet groen.
