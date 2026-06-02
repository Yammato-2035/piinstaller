# Rescue ISO — Build Readiness nach App-Decomposition

**Stand:** 2026-06-02  
**ISO-Build in diesem Lauf:** nein  
**QEMU / USB:** nein

## Status

**`ready_for_controlled_iso_build_precheck`** mit Einschränkung **`blocked_by_deploy_drift`** für Live-Runtime-Diagnose.

| Kriterium | Ergebnis |
|-----------|----------|
| App-Bootstrap (Factory, Middleware, Router-Registry) | Workspace OK, Import/py_compile OK |
| Startup-Diagnostik / Version-Felder | Code vorhanden; live nach Deploy |
| Core-Facades (storage, mount, safety) | vorhanden + pytest |
| Boundary-Guard | `review_required` (app.py noch groß) |
| Runtime-Gate profilbewusst | OK |
| Deploy-Drift Workspace vs `/opt` | **offen** |
| Rescue-Agent live | nicht behauptet (kein Smoke) |
| Bootmenü-Branding-Precheck | unverändert aus `RESCUE_BOOT_MENU_BRANDING_PRECHECK.md` |

## Bedeutung

`ready_for_controlled_iso_build_precheck` = Architektur-Risiko für den **nächsten** kontrollierten ISO-Precheck reduziert — **nicht** „ISO gebaut“ oder „USB bereit“.

## Empfohlene Reihenfolge

1. Operator-Deploy-Sync + kontrollierter Backend-Reload  
2. `check-runtime-deploy-gate.sh` / `deploy_drift` grün  
3. Controlled ISO build precheck (ohne USB)  
4. Erst danach ISO-Build-Lauf mit Operator-Freigabe
