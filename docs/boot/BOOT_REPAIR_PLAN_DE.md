# Boot Repair Plan (DE)

## Ziel
Aus `post_verify` + `boot_capability` + `inspect` wird ein strukturierter Reparatur-**Plan** erzeugt.
Es werden **keine** Reparaturen ausgeführt.

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

## Regeln in Phase 1
- nur Analyse + Vorschläge
- `auto_allowed` immer `false`
- keine Execute-Route
- Windows/Dualboot immer defensiv (manual review)
