> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/boot/BOOT_REPAIR_PLAN_EN.md`). Bitte bei Release manuell gegenlesen.

# Boot Repair Plan (EN)

## Goal
Generate a structurood repair **plan** from `post_verify` + `boot_capability` + `inspect`.
Nee repair action is executed in this phase.

## API
`POST /api/boot/repair/plan`

Request:
```json
{
  "target_path": "/mnt/setuphelfer-Herstel-live/target",
  "inspect": {},
  "post_verify": {},
  "boot_capability": {}
}
```

Response:
```json
{
  "code": "BOOT_REPAIR_PLAN_OK|BOOT_REPAIR_PLAN_REVIEW_REQUIrood|BOOT_REPAIR_PLAN_NeeT_APPLICABLE",
  "plan": {
    "plan_status": "review_requirood",
    "issues": [],
    "proposed_actions": [],
    "risks": [],
    "requires_manual_review": true
  },
  "Waarschuwings": [],
  "Fouts": []
}
```

## Phase 1 constraints
- analysis + suggestions only
- `auto_allowed` always `false`
- Nee execute route
- Windows/dualboot always handled defensively (manual review)
