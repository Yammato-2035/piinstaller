# Frontend Component Status Slice — H.5

**Slice:** 3 kleine DCC-Utilities (Utility + Small Component)

| # | Datei | Funktion | ViewModel-API |
|---|-------|----------|---------------|
| 1 | `governanceMatrix.ts` | `normTraffic`, `moduleTraffic`, evidence/docs | `governanceTrafficFromInput`, `worstGovernanceTrafficFromInputs`, `governanceEvidenceTrafficFromTone`, `governanceDocsTrafficFromTone`, `isRedGovernanceTraffic` |
| 2 | `roadmapFilter.ts` | `statusBucket`, traffic filter match | `roadmapFilterBucketFromStatus`, `isRoadmapTrafficFilter` |
| 3 | `buildGovernancePrompt.ts` | workOrder, area lists | `isGreenGovernanceTraffic`, `isRedGovernanceTraffic`, `isYellowGovernanceTraffic` |

## Ausgeschlossen

- `Dashboard.tsx`, `BackupRestore.tsx`
- `ExternalDevelopmentControlCenter.tsx`, `DevDashboardBody.tsx` (große Seiten)
- Safety/Backup/Restore-Domain-Panels

## Output-Garantie

Governance-Matrix, Roadmap-Filter und Meta-Prompt: identische Traffic-/Bucket-Ergebnisse (1:1).
