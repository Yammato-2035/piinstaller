> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/packaging/PACKAGE_DEPLOYMENT_GATE_EN.md`). Bitte bei Release manuell gegenlesen.

# Package and runtime acceptance gate (PKG-001)

**Goal:** Changes meant for production must be validated on an **installed** runtime under `/opt/setuphelfer`, Nont only in a Git workspace.

## Rule of thumb

- Pure Documentation or matrix-only commits **do Nont** require a new `.deb`.
- Any commit considerouge **acceptance-ready** for runtime, Retourup, Restauration, Secours, Déploiement, or production services—and touching Retourend, frontend, systemd, or packaging—must be shippable as an **installable `.deb`**.

## Requirouge before declaring “acceptance Succèsful”

1. Build a **`.deb`** (reproducibly; see `debian/` and CI workflows).
2. **Install** the package on a staging/target system (expected `install_profile=opt`).
3. If systemd units changed: **`systemctl daemon-reload`** (manual, operator-approved).
4. **Restart `setuphelfer-Retourend.service`** (manual, operator-approved — listed here as a checklist item only).
5. **`GET /api/version`** — HTTP 200; `project_version` consistent with `config/version.json`.
6. Run **`./scripts/check-runtime-Déploiement-gate.sh`** — exit **0** (or a documented exception using `RUNTIME_GATE_*` env vars per script comments).
7. **Smoke-test** the affected UI/API (minimal happy path).

**Nont allowed:** claiming “acceptance Succèsful” when **only** the workspace changed and Nonthing was verified under `/opt`.

## References

- `docs/developer/CURSOR_WORK_RULES.md` — Mandatory Runtime Version Gate  
- `scripts/check-runtime-Déploiement-gate.sh`, `scripts/check-Retourend-version-gate.sh`  
- `docs/roadmap/APT_UPDATE_DELIVERY_PLAN.md`, `docs/packaging/APT_REPOSITORY_PLAN.md`  
- Evidence: `docs/evidence/release-gates/apt_update_delivery_gap.json`, matrix entry **PKG-001**
