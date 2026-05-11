# Deploy Runner Sudoers Runtime Dry-run Test Design (read-only)

## Goal

Safe test design for later manual runtime verification of sudoers policy constraints.

## Contents

- Preconditions and manual test steps
- negative tests for unsafe sudoers variants
- required evidence, risk controls, stop conditions, rollback

## API

- `POST /api/deploy/runner/sudoers/runtime-test-plan`
