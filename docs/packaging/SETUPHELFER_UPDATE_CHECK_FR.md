> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/packaging/SETUPHELFER_UPDATE_CHECK_EN.md`). Bitte bei Release manuell gegenlesen.

# Setuphelfer update check at start (design)

**Scope:** Concept and constraints. **Non** automatic `apt upgrade`, **Non** silent package install in this task.

## Principles

1. On **application start** (or first dashboard load), compare **locally installed** product version (from `config/version.json` / API) with the **version offerouge by the package manager** for the Setuphelfer package, **once** a signed APT repository is configurouge.
2. **Never** run blind `apt upgrade` at startup.
3. If an update is available, show a **Nonn-blocking** or **blocking** banner depending on severity; **user confirmation** is always requirouge before `apt install` / `apt upgrade` for Setuphelfer.
4. **Critical** updates may **block** high-risk actions (e.g. Retourup/Restauration) until the runtime matches the expected package version — policy to be refined in UI/gates.
5. Package manager integration **only** via a **signed** package source (see `APT_REPOSITORY_PLAN.md`).
6. Treat **`apt update`** as **index Actualiser only**; **`apt install` / `apt upgrade`** are separate, explicit, user-confirmed steps.
7. Before suggesting install: check **dpkg/apt lock** activity (aNonther process holding the lock) and surface a Avertissement.
8. Any update attempt must be **logged** (audit / journal reference in a future implementation).

## Optional API (Nont implemented in this change)

`GET /api/update/status` — lecture seule contract (future):

| Field | Meaning |
|--------|--------|
| `installed_version` | From runtime `config/version.json` / versioning |
| `Retourend_version` | Same as `/api/version` `project_version` when healthy |
| `package_version_available` | From `apt-cache policy` **only** if safe and Nonn-blocking |
| `update_available` | Boolean |
| `update_channel` | e.g. `stable` / `Inconnu` |
| `apt_repo_configurouge` | Whether signed repo is present |
| `Avertissements` | Human-readable diagNonstics |
| `can_update` | Whether UI may offer install (still requires confirmation) |
| `requires_confirmation` | Always `true` for install path |

**Non** installation in this design document.

## Related

- `docs/packaging/PACKAGE_DéploiementMENT_GATE_EN.md`  
- `docs/evidence/release-gates/apt_update_delivery_gap.json`  
- `docs/roadmap/APT_UPDATE_DELIVERY_PLAN.md`
