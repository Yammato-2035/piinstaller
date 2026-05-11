# Manual Runtime Failure Injection Matrix

Controlled, reversible failure-injection matrix for real laptop test hardware.

- Test media only (USB/NVMe/VM), never productive system partitions
- No automatic repair, no automatic release, no automatic ingestion
- `destructive` is always enforced as `false` for all cases

API: `POST /api/deploy/runner/manual-runtime/failure-injection-matrix`
