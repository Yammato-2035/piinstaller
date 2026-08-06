# PRE_BUILD_FULL_REGRESSION — PI-RS-ASUS-CARRIER-BUILD-WRITE-004

Stand: 2026-08-06T19:51Z  
Workspace: `/home/volker/piinstaller-asus-emergency-linux-telemetry-003`  
Python: `/home/volker/piinstaller/.venv` (+ httpx)

## Backend-Vollsuite

```bash
source /home/volker/piinstaller/.venv/bin/activate
PYTHONPATH=backend python -m pytest -q backend/tests
```

| Metrik | Ausgang (Baseline) | Aktuell |
|--------|--------------------|---------|
| passed | 4048 | **4070** |
| failed | 9 | **1** |
| skipped | 29 | 29 |

Log: `pre_build_full_regression_pytest.txt`

### Einziger aktueller Fehler

| Feld | Wert |
|------|------|
| Test | `TestMsiWindowsRoutesReadonlyV1::test_capabilities_handler_scope` |
| Datei | `test_msi_windows_routes_readonly_v1.py` |
| Ursache | Event-Loop-Flake (`RuntimeError: There is no current event loop`) |
| Identisch Ausgangsfehler #4 | **ja** |
| Isoliert | **5/5 passed** |
| Build-relevant | nein |
| Write-relevant | nein |
| ASUS-relevant | nein |
| Telemetrie-relevant | nein |
| Safety-relevant | nein |

Die früheren Fehler #1–#3 und #5–#9 sind in diesem Lauf **nicht** mehr aufgetreten
(Remediation + Versionsbump 1.10.2.0 / Payload 1.10.0.17).

### Gate-Bewertung Regression

| Kriterium | Ergebnis |
|-----------|----------|
| Neue Regression | **nein** |
| Veränderte Ursache am verbleibenden Fehler | **nein** (bekannter Flake) |
| Fehler im physischen Pfad | **nein** |
| Targeted Tests grün | **ja** (316) |

## Frontend

| Gate | Ergebnis | Hinweis |
|------|----------|---------|
| Typecheck (`tsc --noEmit`) | exit 2, viele vorbestehende Fehler | wie Baseline-002 |
| Vitest | 2 failed / 172 passed | `rescueStickUsbGate.test.ts` — **identisch Baseline-002** |
| `npm run build` | **exit 0** | Vite-Produktionbuild OK |

## Runtime- / Boundary-Gates

| Gate | Ergebnis |
|------|----------|
| Workspace-Version-Consistency | ok (`1.10.2.0`) |
| `check-runtime-deploy-gate.sh` | exit 0 (legacy Hinweis 404 release) |
| `check-runtime-profile-deploy-gate.sh` | `project_version_mismatch:1.9.21.2!=1.10.2.0` |
| `check-backend-version-gate.sh` | exit **14**, Drift API `1.9.21.2` vs Workspace `1.10.2.0` |
| `check-module-boundaries.sh` | exit 0, `status=review_required` (vorbestehende Warnings) |

**Hinweis:** Host-Runtime unter `/opt/setuphelfer` ist **älter** als Workspace.
Für produktive Host-API-Tests gilt Phase-0-Blocker. Controlled ISO-Build und
USB-Write nutzen den **Workspace-Buildpfad**; USB-Write bleibt zusätzlich an
ISO-Verify + doppelte Operatorbestätigung gebunden.

## USB_WRITE_ALLOWED (Regressionsteil)

`true` bezüglich Testregression (keine neue Suite-Regression, physischer Pfad grün).

Endgültige Write-Freigabe erst nach Controlled-ISO-Verify + Capacity/Safety +
zwei Operatorbestätigungen; Runtime-Drift bleibt als Host-Hinweis dokumentiert.
