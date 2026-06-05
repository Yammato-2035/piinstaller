# DCC Blank Screen Triage — Fail-Safe Diagnostics Result

**Datum:** 2026-06-05  
**HEAD vorher:** `5608916`  
**Branch:** `main`

## Phase 0 — Known Error

| Klassifikation | Bekannt? | Anmerkung |
|----------------|----------|-----------|
| `frontend_gating_build_time_desync` | Ja | Fix `4fb72ee` — Gating über Statusroute |
| `profile_block_expected_but_misread_as_down` | Ja | release + 404 ≠ Backend-down |
| `known_operator_port_confusion` | Ja | :8080 ≠ DCC |
| `fix_not_deployed` / `stale_frontend_bundle` | Ja | Dist-Alter vs. Workspace |
| **`blank_dcc_screen`** | **Neu** | Cockpit ohne nutzbaren Inhalt trotz erreichbarer UI |

Frühere Korrektur (`decideDccVisibility`) reichte nicht: Loading/Error-Zustände zeigten nur minimale zentrierte Texte ohne persistente Diagnose — wirkte im Browser wie „leer“.

## Phase 1 — Live-Wahrheit (release, read-only)

| Check | Ergebnis |
|-------|----------|
| `install_profile` | `release` |
| `dev_control_enabled` | `false` |
| `/api/dev-dashboard/status` | HTTP **404** `PROFILE_ROUTE_BLOCKED` (erwartet) |
| UI `:3001/?window=cockpit` | HTTP **200** |
| `/opt` Dist (vor diesem Fix-Deploy) | `dev-dashboard/status` + Retry-Label vorhanden; **`DCC_BOOT_DIAGNOSTICS_V1` fehlte** |

**Klassifikation vor Fix:** Unter release ist `profile_blocked_release` erwartet — kein Portfehler. Blank-Screen unter local_lab oder nach Renderfehler = eigener Blocker.

## Implementierter Fix

1. **`dccBootState.ts`** — sieben Boot-States + `classifyDccBootState()`
2. **`DccBootDiagnosticsPanel.tsx`** — immer sichtbar (URL, API-Base, Version/Status-HTTP, Ports, Bundle-Marker, Retry nur Fetch)
3. **`DccErrorBoundary.tsx`** — `frontend_runtime_error` mit Stack + Diagnose
4. **`ExternalDevelopmentControlCenter.tsx`** — nie leere Seite; Shell mit Diagnose + klassifiziertem Body
5. **Bundle-Marker** `DCC_BOOT_DIAGNOSTICS_V1` in `dccGate.ts` + Vite define

## Tests

- `npm --prefix frontend run build`: OK
- `npm --prefix frontend run test -- --run`: **67/67** OK (`dccBootState.test.ts`, `dccGate.test.ts`)

## Deploy / Live-Acceptance

| Schritt | Status |
|---------|--------|
| Commit | ausstehend (dieser Lauf) |
| Deploy `/opt` | Operator (`sudo`) |
| local_lab Browser-Smoke | Operator |
| release restore | Operator |

## Ampel

**`yellow`** nach Commit — Diagnosepanel garantiert sichtbar; DCC-Inhalt unter local_lab erst nach Operator-Deploy + Profilwechsel grün.

## Operator-Handoff

```bash
cd /home/volker/piinstaller
sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller

grep -R "DCC_BOOT_DIAGNOSTICS_V1\|dcc-boot-diagnostics" /opt/setuphelfer/frontend/dist/assets/*.js | head -5

# local_lab + Browser — siehe DCC_FRONTEND_PROFILE_DESYNC_LIVE_ACCEPTANCE_RESULT.md
# release restore zwingend danach
```

**Pflicht:** Leerer Browser = `blank_dcc_screen_unresolved` — blockiert Monolith-Aufteilung.
