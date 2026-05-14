# Setuphelfer update check at start (design)

**Scope:** Concept and constraints. **No** automatic `apt upgrade`, **no** silent package install in this task.

## Principles

1. On **application start** (or first dashboard load), compare **locally installed** product version (from `config/version.json` / API) with the **version offered by the package manager** for the Setuphelfer package, **once** a signed APT repository is configured.
2. **Never** run blind `apt upgrade` at startup.
3. If an update is available, show a **non-blocking** or **blocking** banner depending on severity; **user confirmation** is always required before `apt install` / `apt upgrade` for Setuphelfer.
4. **Critical** updates may **block** high-risk actions (e.g. backup/restore) until the runtime matches the expected package version — policy to be refined in UI/gates.
5. Package manager integration **only** via a **signed** package source (see `APT_REPOSITORY_PLAN.md`).
6. Treat **`apt update`** as **index refresh only**; **`apt install` / `apt upgrade`** are separate, explicit, user-confirmed steps.
7. Before suggesting install: check **dpkg/apt lock** activity (another process holding the lock) and surface a warning.
8. Any update attempt must be **logged** (audit / journal reference in a future implementation).

## Optional API (not implemented in this change)

`GET /api/update/status` — read-only contract (future):

| Field | Meaning |
|--------|--------|
| `installed_version` | From runtime `config/version.json` / versioning |
| `backend_version` | Same as `/api/version` `project_version` when healthy |
| `package_version_available` | From `apt-cache policy` **only** if safe and non-blocking |
| `update_available` | Boolean |
| `update_channel` | e.g. `stable` / `unknown` |
| `apt_repo_configured` | Whether signed repo is present |
| `warnings` | Human-readable diagnostics |
| `can_update` | Whether UI may offer install (still requires confirmation) |
| `requires_confirmation` | Always `true` for install path |

**No** installation in this design document.

## Related

- `docs/packaging/PACKAGE_DEPLOYMENT_GATE_EN.md`  
- `docs/evidence/release-gates/apt_update_delivery_gap.json`  
- `docs/roadmap/APT_UPDATE_DELIVERY_PLAN.md`
