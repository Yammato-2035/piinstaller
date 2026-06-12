# KB: DCC Aggregation Audit F.3

Short summary for operators and developers.

## What was audited?

After F.1 (facade) and F.2 (6 route migrations), **without code changes**:

- remaining direct DCC core access
- duplicate traffic-light/status logic
- roadmap subrouter boundary
- AI prompt stub
- deploy/core coupling

## Key findings

1. **`dcc_status_facade`** remains the HTTP aggregation entry for migrated routes.
2. **`POST /api/ai/prompt/generate`** should use the same facade as `GET cursor-meta-prompt` in F.4.
3. **Roadmap subroutes** may call `load_roadmap_registry_bundle` directly — registry-only slices.
4. **`deploy_job_state`** still reads `build_dashboard_status` directly — facade hook medium-term.
5. **Frontend** lacks central `dccStatusViewModel` — duplicate risk with backend mappings.

## Next safe migration

**F.4:** `ai_prompt_generate_stub` → `build_dcc_cursor_meta_prompt_api()`

Full doc: [DCC_AGGREGATION_AUDIT_F3_EN.md](../../architecture/DCC_AGGREGATION_AUDIT_F3_EN.md)
