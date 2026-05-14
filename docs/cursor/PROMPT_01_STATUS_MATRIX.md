# Prompt 01 – Statusmatrix

## PHASE 0 – Mandatory Runtime Version Gate (Pflicht)

1. `./scripts/check-runtime-deploy-gate.sh` (Exit **0**), falls vorhanden; sonst `./scripts/check-backend-version-gate.sh` plus `GET /api/dev-dashboard/status` (`deploy_drift`) manuell.
2. Bei Exit **≠ 0**: **STOP** — kein produktiver Schritt gegen `/opt` oder Port **8000**; Abschlussbericht **`blocked_runtime_outdated`** + Gate-Log; `docs/developer/CURSOR_WORK_RULES.md`.

---

Aktualisiere `docs/roadmap/STATUS_MATRIX.md` anhand von:

- `docs/testing/*.md`
- `docs/evidence/**`
- offenen GitHub-Issues (falls vorhanden)

Regeln:

- Grün nur mit Evidence.
- Blocker mit P0–P3 klassifizieren.
- Kein Produktcode ändern, außer es ist ausdrücklich ein Bugfix außerhalb dieses Prompts freigegeben.

Output: kurze Delta-Liste was sich geändert hat.
