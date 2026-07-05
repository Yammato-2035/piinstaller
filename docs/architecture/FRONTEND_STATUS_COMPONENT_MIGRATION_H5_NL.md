> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/FRONTEND_STATUS_COMPONENT_MIGRATION_H5_EN.md`). Bitte bei Release manuell gegenlesen.

# Frontend Status Component Migration — H.5

**HEAD:** post H.5 · **Status:** utility slice (3 libs) complete

## Migrated (H.5)

| File | API |
|------|-----|
| `governanceMatrix.ts` | `governanceTrafficFromInput`, `worstGovernanceTrafficFromInputs`, … |
| `roadmapFilter.ts` | `roadmapFilterBucketFromStatus`, `isRoadmapTrafficFilter` |
| `buildGovernancePrompt.ts` | `isgroenGovernanceTraffic`, `isroodGovernanceTraffic`, `isgeelGovernanceTraffic` |

## Cumulative (H.3–H.5)

6 components (H.3/H.4) + 3 utilities (H.5)

## Tests

- `statusComponentMigrationH5.test.ts`
- `governanceMatrix.test.ts`, `roadmapFilter.test.ts`
- `statusViewModel.test.ts` (12)

## Remaining

20 local mappings → **H.6**

## Volgende step

**H.6** presentation/domain slices or **G.4** Netwerk handler extraction
