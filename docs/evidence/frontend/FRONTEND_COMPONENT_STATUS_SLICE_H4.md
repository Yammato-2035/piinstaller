# Frontend Component Status Slice — H.4

**Slice:** 3 kleine Komponenten (zweiter Migrations-Slice)

| # | Datei | Funktion | ViewModel-API |
|---|-------|----------|---------------|
| 1 | `ReadyStableSection.tsx` | `isGreenStatus` | `isDashboardGreenStatus` |
| 2 | `StatusCard.tsx` | `isOk` | `dashboardToneFromInput` + `isGreenDashboardTone` |
| 3 | `RiskWarningCard.tsx` | `defaultTitle` | `riskWarningTitleKeyForLevel` |

## Ausgeschlossen

- `BackupRestore.tsx`, `Dashboard.tsx`
- `RoadmapDrawer.tsx` (abweichende CSS-Klassen)
- `DocumentationDiagnosticsCard.tsx` (Domain-Heuristik)
- `CockpitBackupTargetPanel.tsx` (Backup-Domain)
- `PartitionSafetyStatusPanel.tsx` (Safety/Restore-Domain)
- `BackendHealthPanel.tsx` (kein `=== green/red/yellow`-Pattern; `status === 'ok'`)

## Neue ViewModel-Helfer (H.4)

- `isDashboardGreenStatus` — Runtime-Gate/Deploy-Drift grün-stable
- `isGreenDashboardTone` — OK-Hervorhebung in StatusCard
- `riskWarningTitleKeyForLevel` — i18n-Key für RiskWarningCard

## Output-Garantie

Alle drei Komponenten: Props, CSS-Klassen, sichtbare Texte unverändert (1:1).
