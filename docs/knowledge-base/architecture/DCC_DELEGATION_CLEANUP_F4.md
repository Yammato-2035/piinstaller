# KB: DCC Delegation Cleanup F.4

F.4 schließt die letzte sichere DCC-HTTP-Delegation ab.

## Was wurde migriert?

1. **AI Prompt Stub** nutzt dieselbe Facade wie `GET cursor-meta-prompt`
2. **Readonly-Router** (backend-health, notifications, evidence-index) nutzt Facade-API-Helper

## Was bleibt?

- Roadmap-Subroutes (reine Registry)
- `deploy_job_state` Runtime-Gate (Core, nicht HTTP)

Vollständig: [DCC_DELEGATION_CLEANUP_F4.md](../../architecture/DCC_DELEGATION_CLEANUP_F4.md)
