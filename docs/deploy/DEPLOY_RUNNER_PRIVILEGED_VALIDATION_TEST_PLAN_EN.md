# Deploy Runner Privileged Validation Dry-run Test Design (read-only)

## Goal

Concrete test design for later privileged runner validation in dry-run mode without real write operations.

## Contents

- Preconditions, manual test steps, and negative tests
- required evidence including UID/GID, audit, and lock proofs
- risk controls, stop conditions, and rollback

## API

- `POST /api/deploy/runner/privileged-validation/test-plan`
