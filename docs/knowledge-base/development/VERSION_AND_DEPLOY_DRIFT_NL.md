# Versie- en deploy-drift (KB)

**Task:** PI-RS-BVR-GUI-DCC-001

## Bron van waarheid

- `config/version.json` → `project_version`
- `config/rescue_payload_version.json` → `rescue_payload_version`
- Deploy-manifesten (workspace + `/opt/setuphelfer`)

## Verkeerslichten

| Kleur | Betekenis |
|-------|-----------|
| GREEN | Identiteiten kloppen |
| YELLOW | Gedocumenteerde achterstand |
| RED | Onverwachte afwijking |
| GRAY | Onbekend — **niet** als OK behandelen |

## Phase 0

```bash
./scripts/check-runtime-deploy-gate.sh
python3 backend/tools/check_version_consistency.py --repo-root .
```

## Zie ook

- [VERSION_COMMIT_DRIFT_CONTRACT.md](../../architecture/VERSION_COMMIT_DRIFT_CONTRACT.md)
