# APT update delivery plan (roadmap)

**Status:** not production-ready for automatic end-user updates until a package channel exists.

## Facts

- **`apt update`** refreshes package **indexes only**. It does **not** install or upgrade Setuphelfer.
- **`apt upgrade`** / **`apt install setuphelfer`** apply package actions only when a suitable **`.deb`** is available from a configured repository (or local install).

## Required building blocks

1. Reproducible **`.deb`** build (CI artefact).
2. Stable **package name** (e.g. `setuphelfer`).
3. Version alignment with **`config/version.json`** / changelog policy.
4. **`postinst` / `prerm` / `postrm`** scripts (migrations, safe defaults).
5. **systemd** restart/reload policy (`daemon-reload`, service name).
6. **Migration** path for `/opt/setuphelfer/config/version.json` (schema `version_source_of_truth`).
7. **APT repository** or other signed distribution channel.
8. **GPG** signing for repository metadata and/or packages.
9. **Automated update tests** (install, restart, `/api/version` gate).
10. **Rollback** strategy (package pinning, previous `.deb`, operator runbook).

## Ampel

| Topic | Colour |
|-------|--------|
| Gate + runbook for `/opt` manual path | Yellow/Green (process) |
| APT repo + signed channel | Red until implemented |

See also: `docs/packaging/APT_REPOSITORY_PLAN.md`, `docs/evidence/release-gates/apt_update_delivery_gap.json`.
