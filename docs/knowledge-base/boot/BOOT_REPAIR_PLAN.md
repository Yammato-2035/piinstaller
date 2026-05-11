# Boot Repair Plan

## Purpose
Provide structured next-step suggestions without executing any repair action.

## Inputs
- post-restore validation result
- boot capability result
- inspect classification hints

## Outputs
- issue codes
- proposed action objects (always `auto_allowed=false`)
- risk codes
- manual review requirement flag

## Safety posture
- Windows/dualboot: always manual-review-first
- unknown or conflicting layouts: manual review + high caution
- no write operations in this phase
