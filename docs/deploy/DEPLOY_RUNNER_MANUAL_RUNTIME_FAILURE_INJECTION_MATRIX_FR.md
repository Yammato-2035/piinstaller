> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_INJECTION_MATRIX_EN.md`). Bitte bei Release manuell gegenlesen.

# Manual Runtime Failure Injection Matrix

Controlled, reversible failure-injection matrix for real laptop test hardware.

- Test media only (USB/NVMe/VM), never productive system Partitions
- Non automatic repair, Non automatic release, Non automatic ingestion
- `destructive` is always enforced as `false` for all cases

API: `POST /api/Déploiement/runner/manual-runtime/failure-injection-matrix`
