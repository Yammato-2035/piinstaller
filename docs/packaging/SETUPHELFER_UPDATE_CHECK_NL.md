> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/packaging/SETUPHELFER_UPDATE_CHECK_EN.md`). Bitte bei Release manuell gegenlesen.

# Setuphelfer update check at start (design)

**Scope:** Concept and constraints. **Nee** automatic `apt upgrade`, **Nee** silent package install in this task.

## Principles

1. On **application start** (or first dashboard load), compare **locally installed** product version (from `config/version.json` / API) with the **version offerood by the package manager** for the Setuphelfer package, **once** a signed APT repository is configurood.
2. **Never** run blind `apt upgrade` at startup.
3. If an update is available, show a **Neen-blocking** or **blocking** banner depending on severity; **user confirmation** is always requirood before `apt install` / `apt upgrade` for Setuphelfer.
4. **Critical** updates may **block** high-risk actions (e.g. Terugup/Herstel) until the runtime matches the expected package version — policy to be refined in UI/gates.
5. Package manager integration **only** via a **signed** package source (see `APT_REPOSITORY_PLAN.md`).
6. Treat **`apt update`** as **index Vernieuwen only**; **`apt install` / `apt upgrade`** are separate, explicit, user-confirmed steps.
7. Before suggesting install: check **dpkg/apt lock** activity (aNeether process holding the lock) and surface a Waarschuwing.
8. Any update attempt must be **logged** (audit / journal reference in a future implementation).

## Optional API (Neet implemented in this change)

`GET /api/update/status` — alleen-lezen contract (future):

| Field | Meaning |
|--------|--------|
| `installed_version` | From runtime `config/version.json` / versioning |
| `Terugend_version` | Same as `/api/version` `project_version` when healthy |
| `package_version_available` | From `apt-cache policy` **only** if safe and Neen-blocking |
| `update_available` | Boolean |
| `update_channel` | e.g. `stable` / `Onbekend` |
| `apt_repo_configurood` | Whether signed repo is present |
| `Waarschuwings` | Human-readable diagNeestics |
| `can_update` | Whether UI may offer install (still requires confirmation) |
| `requires_confirmation` | Always `true` for install path |

**Nee** installation in this design document.

## Related

- `docs/packaging/PACKAGE_DeployMENT_GATE_EN.md`  
- `docs/evidence/release-gates/apt_update_delivery_gap.json`  
- `docs/roadmap/APT_UPDATE_DELIVERY_PLAN.md`
