# Deploy Execute Prep

Deploy Execute Prep adds session/token/plan/profile/target binding for deploy operations, but deliberately does **not** execute any installation logic yet.

## API

- `POST /api/deploy/session` creates a short-lived session tied to:
  - target device
  - selected profile
  - plan snapshot hash
  - confirmation token
- `POST /api/deploy/execute` performs readiness checks only and returns `DEPLOY_EXECUTE_READY`.

## Guarantees in this phase

- no partitioning
- no formatting
- no image writes
- no package install/download
- no mounts/chroot
- no service/network mutation
