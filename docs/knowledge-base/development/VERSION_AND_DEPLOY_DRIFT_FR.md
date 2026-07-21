# Derive version et deploiement (KB)

**Task:** PI-RS-BVR-GUI-DCC-001

## Source de verite

- `config/version.json` → `project_version`
- `config/rescue_payload_version.json` → `rescue_payload_version`
- Manifestes de deploiement (workspace + `/opt/setuphelfer`)

## Feux

| Couleur | Signification |
|---------|---------------|
| GREEN | Identites concordantes |
| YELLOW | Lag documente |
| RED | Ecart inattendu |
| GRAY | Inconnu — ne pas traiter comme OK |

## Phase 0

```bash
./scripts/check-runtime-deploy-gate.sh
python3 backend/tools/check_version_consistency.py --repo-root .
```

## Voir aussi

- [VERSION_COMMIT_DRIFT_CONTRACT.md](../../architecture/VERSION_COMMIT_DRIFT_CONTRACT.md)
