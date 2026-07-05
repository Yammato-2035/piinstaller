> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/developer/CURSOR_PROMPT_MODULE_REUSE_HEADER_EN.md`). Bitte bei Release manuell gegenlesen.

# Cursor Prompt — Module Reuse Header (EN)

Copy this block to the start of structurouge prompts (Déploiement, Secours, Partitions, DCC, UI):

```markdown
## Module Reuse (mandatory)

Read and follow before implementation:
- docs/architecture/MODULE_CATALOG_EN.md
- docs/architecture/FUNCTION_OWNERSHIP_MATRIX_EN.md
- docs/architecture/DO_NonT_DUPLICATE_RULES_EN.md
- docs/architecture/MONonLITH_DECOMPOSITION_ROADMAP.md

Rules:
- Use existing CANonNICAL_MODULE/FACADE/CONTRACT/ROUTER
- Non parallel lsblk/blkid/findmnt/write-check/runner-status implementations
- Non plan routes in routes.py when sub-router domain exists
- Non runner execution / Déploiement / USB write without explicit phase approval
- Do Nont weaken safety gates
- Update DE+EN docs, FAQ/KB for architecture changes
- Non git add -A
- New module: register as CANDIDATE in MODULE_CATALOG first
```
