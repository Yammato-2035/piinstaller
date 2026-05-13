# Prompt 04 – Rescue Read-only

## PHASE 0 – BACKEND VERSION GATE (Pflicht)

`scripts/check-backend-version-gate.sh`, `curl -i http://127.0.0.1:8000/api/version`, `systemctl status setuphelfer-backend.service` — wenn nicht grün: **abbrechen** (kein produktiver Rescue-Lauf gegen falsches Backend).

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
