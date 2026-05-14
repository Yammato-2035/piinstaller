# Paket- und Runtime-Abnahme-Gate (PKG-001)

**Ziel:** Abnahmefähige Änderungen müssen auf einer **installierten** Runtime unter `/opt/setuphelfer` nachweisbar sein — nicht nur im Git-Workspace.

## Grobe Regel

- Reine **Doku-/Matrix-Commits** erzwingen **kein** neues `.deb`.
- Jeder Commit, der für **Runtime**, Backup, Restore, Rescue, Deploy oder produktive Dienste **abgenommen** werden soll und Backend, Frontend, systemd oder Packaging betrifft, muss als **installierbares `.deb`** lieferbar sein.

## Pflicht vor der Formulierung „Abnahme erfolgreich“

1. **`.deb` bauen** (reproduzierbar; siehe `debian/` und CI-Workflows).
2. **Lokal/staging installieren** (erwartetes `install_profile=opt`).
3. Bei geänderten Units: **`systemctl daemon-reload`** (manuell, mit Freigabe).
4. **`setuphelfer-backend.service` neu starten** (manuell, mit Freigabe — hier nur Checklistenpunkt, **kein** automatischer Restart durch diese Doku).
5. **`GET /api/version`** — HTTP 200; `project_version` konsistent zu `config/version.json`.
6. **`./scripts/check-runtime-deploy-gate.sh`** — Exit **0** (oder dokumentierte Ausnahme mit `RUNTIME_GATE_*` laut Skriptkommentar).
7. **Smoke-Test** der betroffenen UI/API (minimaler Happy Path).

**Verboten:** „Abnahme erfolgreich“, wenn **nur** der Workspace geändert und **nichts** unter `/opt` verifiziert wurde.

## Verweise

- `docs/developer/CURSOR_WORK_RULES.md` — Mandatory Runtime Version Gate  
- `scripts/check-runtime-deploy-gate.sh`, `scripts/check-backend-version-gate.sh`  
- `docs/roadmap/APT_UPDATE_DELIVERY_PLAN.md`, `docs/packaging/APT_REPOSITORY_PLAN.md`  
- Evidence: `docs/evidence/release-gates/apt_update_delivery_gap.json`, Matrix **PKG-001**
