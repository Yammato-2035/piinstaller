# Operator-Runbook: Runtime Deploy & Drift

**Kontext:** PI-RS-BVR-GUI-DCC-001 und allgemeine Phase-0-Prüfungen vor Rescue-/Runtime-Tests.

## Wann anwenden

Vor jedem Test gegen produktive Runtime (`/opt/setuphelfer`), Hardware-Boot oder Deploy-Verify.

## Phase-0-Checkliste

1. **Runtime Gate**

```bash
./scripts/check-runtime-deploy-gate.sh
# alternativ / zusätzlich:
./scripts/check-backend-version-gate.sh
```

Exit **0** erforderlich. Bei Fehler: **STOP** — kein Hardwaretest.

2. **API-Version**

```bash
curl -fsS http://127.0.0.1:8000/api/version | jq .
```

- HTTP 200
- `project_version` = `config/version.json` → `project_version`
- `backend_runtime_path` zeigt auf `/opt/setuphelfer/backend` (bei Produktivtest)

3. **Version-Konsistenz (Workspace)**

```bash
python3 backend/tools/check_version_consistency.py --repo-root .
```

4. **Deploy-Drift**

Development Cockpit: `deploy_drift` — keine roten Abweichungen für den Auftrag relevanten Kerndateien.

5. **Dienst aktiv**

```bash
systemctl is-active setuphelfer-backend.service
```

6. **Runtime nicht älter als erwarteter Commit**

```bash
git -C /opt/setuphelfer rev-parse HEAD
git rev-parse HEAD   # Workspace
```

## Drift-Ampeln (Kurz)

| Farbe | Bedeutung | Aktion |
|-------|-----------|--------|
| GREEN | Identitäten stimmen | Test freigeben |
| YELLOW | Dokumentierter Lag (Feature vs. main, GUI-Fallback) | Bewusst weiter; dokumentieren |
| RED | Unerwartete Abweichung | Deploy/Update vor Test |
| GRAY | Unbekannt | Evidence/Runtime ermitteln; nicht als OK werten |

## Typische Drifts

- **Workspace ≠ /opt:** Runtime deployen oder Test auf Workspace beschränken (nur Unit-Tests).
- **Payload ≠ USB:** Stick neu schreiben mit Ziel-Payload (`1.10.1.1` für DCC-001).
- **API-Version driftet:** Backend-Dienst neu starten nach Deploy.

## Rescue-Payload-SoT

`config/rescue_payload_version.json` → `rescue_payload_version`  
Unabhängig von `project_version` — Stick-Builds referenzieren Payload-Version.

## Nach Deploy

1. Gate erneut ausführen.
2. DCC Drift-Matrix prüfen (`version_drift_status`, `deploy_drift_status`).
3. Erst dann physischer Rescue-/MSI-Test.

## Siehe auch

- [VERSION_COMMIT_DRIFT_CONTRACT.md](../architecture/VERSION_COMMIT_DRIFT_CONTRACT.md)
- [docs/dev-dashboard/PHASE0_RUNTIME_GATE.md](../dev-dashboard/PHASE0_RUNTIME_GATE.md)
