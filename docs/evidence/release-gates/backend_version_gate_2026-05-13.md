# Release gate — Backend version update (2026-05-13)

## Summary

A **read-only** gate (`scripts/check-backend-version-gate.sh`) and strengthened **`GET /api/version`** behaviour document the required runtime before backup/restore/hardware evidence runs.

## Gate green when

- `setuphelfer-backend.service` is **active**
- **`GET /api/version`** returns **HTTP 200** and `status":"success"`
- Production **`/opt/setuphelfer/config/version.json`** contains **`version_source_of_truth": true`**
- Workspace `config/project_version` matches API `project_version` (script check)
- Critical files exist under `/opt/setuphelfer/backend/`

## Gate red / blocked

- HTTP **503** from `/api/version` with `backend.version_config_invalid` or `backend.update_required`
- Script exit **≠ 0** (see script header for codes 10–20)

## APT delivery

Automatic end-user updates are **not** green without a `.deb` channel — see **`apt_update_delivery_gap.json`** and **`docs/roadmap/APT_UPDATE_DELIVERY_PLAN.md`**.

## No backup executed

This change set is documentation, scripts, API diagnostics, and tests only.
