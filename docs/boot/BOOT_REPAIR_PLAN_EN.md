# Boot Repair Plan (EN)

## Goal
Generate a structured repair **plan** from `post_verify` + `boot_capability` + `inspect`.
No repair action is executed in this phase.

## API
`POST /api/boot/repair/plan`

Request:
```json
{
  "target_path": "/mnt/setuphelfer-restore-live/target",
  "inspect": {},
  "post_verify": {},
  "boot_capability": {}
}
```

Response:
```json
{
  "code": "BOOT_REPAIR_PLAN_OK|BOOT_REPAIR_PLAN_REVIEW_REQUIRED|BOOT_REPAIR_PLAN_NOT_APPLICABLE",
  "plan": {
    "plan_status": "review_required",
    "issues": [],
    "proposed_actions": [],
    "risks": [],
    "requires_manual_review": true
  },
  "warnings": [],
  "errors": []
}
```

## Phase 1 constraints
- analysis + suggestions only
- `auto_allowed` always `false`
- no execute route
- Windows/dualboot always handled defensively (manual review)
