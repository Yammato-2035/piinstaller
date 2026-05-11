# Deploy Write Plan (EN)

## Goal

Simulate a future deploy write flow to a target device without any real disk write.

## Properties

- simulation-only plan
- repeated safety gates
- code-based API responses
- every simulated operation has `auto_allowed=false`

## Hard blocks

- missing target / session mismatch
- system disk, live system
- Windows, dualboot
- unknown device
- non-empty target
- invalid image inspect result

## Important note

This phase performs no writing, partitioning, formatting, or image write.
