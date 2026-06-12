# KB: DCC Delegation Cleanup F.4

F.4 completes the last safe DCC HTTP delegation.

## What was migrated?

1. **AI prompt stub** uses the same facade as `GET cursor-meta-prompt`
2. **Readonly router** (backend-health, notifications, evidence-index) uses facade API helpers

## What remains?

- Roadmap subroutes (registry-only)
- `deploy_job_state` runtime gate (core, not HTTP)

Full doc: [DCC_DELEGATION_CLEANUP_F4_EN.md](../../architecture/DCC_DELEGATION_CLEANUP_F4_EN.md)
