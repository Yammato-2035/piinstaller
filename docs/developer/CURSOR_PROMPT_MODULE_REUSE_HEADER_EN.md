# Cursor Prompt — Module Reuse Header (EN)

Copy this block to the start of structured prompts (deploy, rescue, partitions, DCC, UI):

```markdown
## Module Reuse (mandatory)

Read and follow before implementation:
- docs/architecture/MODULE_CATALOG_EN.md
- docs/architecture/FUNCTION_OWNERSHIP_MATRIX_EN.md
- docs/architecture/DO_NOT_DUPLICATE_RULES_EN.md
- docs/architecture/MONOLITH_DECOMPOSITION_ROADMAP.md

Rules:
- Use existing CANONICAL_MODULE/FACADE/CONTRACT/ROUTER
- No parallel lsblk/blkid/findmnt/write-check/runner-status implementations
- No plan routes in routes.py when sub-router domain exists
- No runner execution / deploy / USB write without explicit phase approval
- Do not weaken safety gates
- Update DE+EN docs, FAQ/KB for architecture changes
- No git add -A
- New module: register as CANDIDATE in MODULE_CATALOG first
```
