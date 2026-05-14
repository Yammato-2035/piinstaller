# Prompt 04 – Rescue Read-only

## PHASE 0 – Mandatory Runtime Version Gate (Pflicht)

`./scripts/check-runtime-deploy-gate.sh` (Exit 0) oder Mindest-Set `./scripts/check-backend-version-gate.sh` + `GET /api/dev-dashboard/status`. Bei Exit **≠ 0**: **STOP** — kein produktiver Rescue-Lauf; **`blocked_runtime_outdated`**.

STRICT MODE – RESCUE READONLY VALIDATION PREP

ZIEL:
Rescue-Stick-Matrix und Read-only-Regeln; kein ISO-Build ohne Freigabe.

NICHT ERLAUBT:
- kein ISO-Build ohne explizite Freigabe
- kein chroot, debootstrap, dd, mount, Restore
- keine Writes auf interne Medien

PHASE 1: `docs/testing/RESCUE_STICK_TEST_MATRIX.md`

PHASE 2: Read-only-Regeln dokumentieren (interne Platten, nur Verify/Bericht)

PHASE 3: RS-001–RS-008 inkl. Evidence-Templates

PHASE 4: `docs/evidence/rescue-stick/` ergänzen (`read_only_requirements.json`, `debian_live_decision.md`, …)

ABSCHLUSSBERICHT: Matrix, Regeln, Templates, Blocker.
