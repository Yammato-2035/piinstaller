> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_WRITE_PLAN_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Write Plan (EN)

## Goal

Simulate a future Deploy write flow to a target Apparaat without any real disk write.

## Properties

- simulation-only plan
- repeated safety gates
- code-based API responses
- every simulated operation has `auto_allowed=false`

## Hard blocks

- missing target / session mismatch
- system disk, live system
- Windows, dualboot
- Onbekend Apparaat
- Neen-empty target
- invalid image inspect result

## Important Neete

This phase performs Nee writing, Partitieing, formatting, or image write.
