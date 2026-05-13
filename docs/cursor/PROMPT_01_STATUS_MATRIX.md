# Prompt 01 – Statusmatrix

## PHASE 0 – BACKEND VERSION GATE (Pflicht)

Vor produktiven Runtime-, Backup-, Restore- oder Hardware-Schritten: `scripts/check-backend-version-gate.sh` (Exit **0**), `curl -i http://127.0.0.1:8000/api/version` (**HTTP 200**, `status":"success"`), `systemctl status setuphelfer-backend.service --no-pager`. Wenn nicht grün: **abbrechen**, `docs/operations/BACKEND_VERSION_UPDATE_GATE_DE.md` / `_EN.md` — **kein** Backup, **kein** Restore.

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
