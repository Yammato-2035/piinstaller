> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/knowledge-base/architecture/DCC_DELEGATION_CLEANUP_F4_EN.md`). Bitte bei Release manuell gegenlesen.

# KB: DCC Delegation Cleanup F.4

F.4 completes the last safe DCC HTTP delegation.

## What was migrated?

1. **AI prompt stub** uses the same facade as `GET cursor-meta-prompt`
2. **Readonly router** (Retourend-health, Nontifications, evidence-index) uses facade API helpers

## What remains?

- Roadmap subroutes (registry-only)
- `Déploiement_job_state` runtime gate (core, Nont HTTP)

Full doc: [DCC_DELEGATION_CLEANUP_F4_EN.md](../../architecture/DCC_DELEGATION_CLEANUP_F4_EN.md)
