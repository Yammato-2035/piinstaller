# Frontend Status Component Migration — H.5

**HEAD:** nach H.5 · **Status:** Utility-Slice (3 Libs) erledigt

## Migriert (H.5)

| Datei | API |
|-------|-----|
| `governanceMatrix.ts` | `governanceTrafficFromInput`, `worstGovernanceTrafficFromInputs`, … |
| `roadmapFilter.ts` | `roadmapFilterBucketFromStatus`, `isRoadmapTrafficFilter` |
| `buildGovernancePrompt.ts` | `isGreenGovernanceTraffic`, `isRedGovernanceTraffic`, `isYellowGovernanceTraffic` |

## Kumulativ (H.3–H.5)

6 Komponenten (H.3/H.4) + 3 Utilities (H.5)

## Tests

- `statusComponentMigrationH5.test.ts`
- `governanceMatrix.test.ts`, `roadmapFilter.test.ts`
- `statusViewModel.test.ts` (12)

## Verbleibend

20 lokale Mappings → **H.6**

## Nächster Schritt

**H.6** Presentation/Domain-Slices oder **G.4** Network Handler Extraction
