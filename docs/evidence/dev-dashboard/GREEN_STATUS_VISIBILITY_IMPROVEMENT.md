# Green Status Visibility Improvement

**Datum:** 2026-05-27

## Geänderte Darstellung (Statuslogik unverändert)

| Komponente | Änderung |
|------------|----------|
| `StatusCard.tsx` | Optional `emphasizeOk`: Ring + „OK“-Badge nur bei `tone=green` |
| `RuntimeGatePanel.tsx` | „OK“-Badge wenn `runtime_gate.passed === true` |
| `ReadyStableSection.tsx` | Gruppiert belegte grüne Bereiche (runtime_gate, deploy_drift, safe_test_mode) mit Evidence-Hinweis |
| `DevelopmentDashboard.tsx` | Ready-Sektion + `emphasizeOk` auf Runtime-Gate-Karte |
| `ExternalDevelopmentControlCenter.tsx` | Ready-Sektion vor Operations-Panels |

## Nicht geändert

- `build_runtime_gate`, `deploy_drift`-Berechnung, Release-Gate, Rescue-Policy
- Keine gelben/roten Bereiche optisch als grün getarnt
- Blocker-Listen in Panels unverändert

## Angezeigte Evidence (read-only)

- `scripts/check-runtime-deploy-gate.sh`
- `GET /api/dev-dashboard/deploy/status`
- Datenquelle (`roadmap_data_source` / `data_source`)

## Rot/gelb bleiben sichtbar

- `release_gate_status: rot`
- `package_gate: red`
- `structure_health: yellow`
- `rescue_iso: yellow`
- Governance-Matrix-Regressions-Panel unverändert
