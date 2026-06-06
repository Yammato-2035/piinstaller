# VERSION_POLICY_ENFORCEMENT_FIX — 1.7.3.1

**Datum:** 2026-06-05  
**Commit:** (nach Abschluss)  
**Push:** nein  
**Deploy erforderlich:** **ja** — `/opt` und `/api/version` melden derzeit noch `1.7.3.0`

## Einordnung (Patch W)

Mehrere Fehlerbehebungen seit `1.7.3.0` ohne Versionsanhebung:

- Deploy-to-opt Post-Verify + Manifest-Erweiterung
- DCC Capability-/Status-Gates, Compact-Status
- Versions-Konsistenz-Gate

Regel: **Fehlerbehebung → 4. Stelle (W)** → `1.7.3.0` → **`1.7.3.1`**

## Version vorher / nachher

| Quelle | Vorher | Nachher |
|--------|--------|---------|
| `config/version.json` | 1.7.3.0 | **1.7.3.1** |
| `VERSION` | 1.7.3.0 | **1.7.3.1** |
| `frontend/package.json` | 1.7.3.0 | **1.7.3.1** |
| `frontend/package-lock.json` (Root) | 1.7.0 (Drift) | **1.7.3.1** |
| Tauri/Cargo Semver | 1.7.3 | **1.7.3** (unverändert, abgeleitet) |
| Paket `.deb` (letzter Build) | SetupHelfer_1.7.3_amd64.deb | **nach neuem Paket-Build:** 1.7.3.1 bzw. Semver 1.7.3 — Gate prüft Workspace/`/opt`, nicht automatisch deb-Dateiname |

## Geänderte Dateien (Auswahl)

- `config/version.json`, `VERSION`, `package.json`, `frontend/package*.json`, Tauri/Cargo
- `frontend/sync-version.js` — `package-lock.json`-Sync
- `backend/core/version_consistency.py`, `backend/tools/check_version_consistency.py`
- `scripts/check-backend-version-gate.sh` — Exit 17/18
- `backend/core/deploy_runtime_verify.py` — Version-Check post-restart
- `docs/developer/VERSIONING.md`, `.cursor/rules/version-policy.mdc`
- Tests: `test_version_consistency_v1.py`, erweitert `test_backend_version_gate_v1.py`

## Tests

| Test | Ergebnis |
|------|----------|
| `pytest test_version_consistency_v1.py test_backend_version_gate_v1.py test_deploy_runtime_verify_v1.py` | (siehe Lauf) |
| `python3 backend/tools/check_version_consistency.py --repo-root .` | Exit 0 erwartet |
| `npm run build` (frontend) | (siehe Lauf) |
| `check-backend-version-gate.sh` | Exit **18** erwartet bis Deploy (Workspace 1.7.3.1 vs `/opt` 1.7.3.0) |

## Operator nach Commit

```bash
sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller
./scripts/check-backend-version-gate.sh   # erwartet Exit 0
curl -sS http://127.0.0.1:8000/api/version | jq .project_version   # 1.7.3.1
```

## Dokumentation

- Regel: `docs/developer/VERSIONING.md`, `.cursor/rules/version-policy.mdc`
- KB: `docs/knowledge-base/deploy/DEPLOY_TO_OPT_RUNTIME_SYNC.md` (Deploy); Versions-Gate in VERSIONING.md
