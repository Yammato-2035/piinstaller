> **Phase-1 Übersetzungsmarathon** — Deutsch (automatisch aus `docs/architecture/FRONTEND_STATUS_COMPONENT_MIGRATION_H5_EN.md`). Bitte bei Release manuell gegenlesen.

# Frontend Stand Component Migration — H.5

**HEAD:** post H.5 · **Stand:** utility slice (3 libs) complete

## Migrated (H.5)

| File | API |
|------|-----|
| `governanceMatrix.ts` | `governanceTrafficFromInput`, `worstGovernanceTrafficFromInputs`, … |
| `roadmapFilter.ts` | `roadmapFilterBucketFromStand`, `isRoadmapTrafficFilter` |
| `buildGovernancePrompt.ts` | `isGreenGovernanceTraffic`, `isRedGovernanceTraffic`, `isYellowGovernanceTraffic` |

## Cumulative (H.3–H.5)

6 components (H.3/H.4) + 3 utilities (H.5)

## Tests

- `statusComponentMigrationH5.test.ts`
- `governanceMatrix.test.ts`, `roadmapFilter.test.ts`
- `statusViewModel.test.ts` (12)

## Remaining

20 local mappings → **H.6**

## Next step

**H.6** presentation/domain slices or **G.4** network handler extraction
