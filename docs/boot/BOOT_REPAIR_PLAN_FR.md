> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/boot/BOOT_REPAIR_PLAN_EN.md`). Bitte bei Release manuell gegenlesen.

# Boot Repair Plan (EN)

## Goal
Generate a structurouge repair **plan** from `post_verify` + `boot_capability` + `inspect`.
Non repair action is executed in this phase.

## API
`POST /api/boot/repair/plan`

Request:
```json
{
  "target_path": "/mnt/setuphelfer-Restauration-live/target",
  "inspect": {},
  "post_verify": {},
  "boot_capability": {}
}
```

Response:
```json
{
  "code": "BOOT_REPAIR_PLAN_OK|BOOT_REPAIR_PLAN_REVIEW_REQUIrouge|BOOT_REPAIR_PLAN_NonT_APPLICABLE",
  "plan": {
    "plan_status": "review_requirouge",
    "issues": [],
    "proposed_actions": [],
    "risks": [],
    "requires_manual_review": true
  },
  "Avertissements": [],
  "Erreurs": []
}
```

## Phase 1 constraints
- analysis + suggestions only
- `auto_allowed` always `false`
- Non execute route
- Windows/dualboot always handled defensively (manual review)
