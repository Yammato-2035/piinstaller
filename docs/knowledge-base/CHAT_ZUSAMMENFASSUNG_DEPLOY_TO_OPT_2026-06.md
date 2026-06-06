# Session-Protokoll — Deploy-to-opt Runtime-Sync (2026-06)

Kuratierte Zusammenfassung der Chat-Runde **DEPLOY_TO_OPT_MISSING_NEW_BACKEND_MODULE_FIX**.  
Vollständige Befehlslisten stehen in der KB/FAQ — hier nur Verlauf und Verweise.

---

## Ausgangslage

- Workspace: neue Backend-Module und Routen (u. a. Compact-Status für internes DCC).
- `/opt/setuphelfer`: älterer Stand — fehlende Module, abweichende SHA256, 404 auf nicht registrierte Routen.

---

## Ergebnis der Analyse

1. **`rsync` in `deploy-to-opt.sh` ist nicht die Ursache** — kein Filter auf `backend/core`.
2. **Wahrscheinlichste Ursache:** Deploy nicht ausgeführt oder aus veralteter Quelle.
3. **Mitverschulden:** Deploy-Manifest-Whitelist unvollständig; keine automatische Post-Deploy-Verifikation.

---

## Umgesetzter Fix (Workspace)

- `backend/core/deploy_runtime_verify.py` + `backend/tools/verify_deploy_to_opt.py`
- Hooks in `scripts/deploy-to-opt.sh` (post-rsync, post-restart)
- Erweiterung `DEPLOY_MANIFEST_REL_PATHS`
- Tests: `backend/tests/test_deploy_runtime_verify_v1.py`
- Evidence: `docs/evidence/dev-dashboard/DEPLOY_TO_OPT_MISSING_NEW_BACKEND_MODULE_FIX.md`

---

## Dokumentation (Trennung öffentlich / intern)

| Ziel | Datei |
|------|--------|
| Wissensdatenbank (allgemein) | [deploy/DEPLOY_TO_OPT_RUNTIME_SYNC.md](deploy/DEPLOY_TO_OPT_RUNTIME_SYNC.md) |
| FAQ (allgemein) | [../faq/RUNTIME_OPT_DEPLOY_FAQ_DE.md](../faq/RUNTIME_OPT_DEPLOY_FAQ_DE.md) |
| DCC / Dev-Server (intern) | [../dev-dashboard/internal/SESSION_COLLECTOR_2026-06-05_DEPLOY_DCC.md](../dev-dashboard/internal/SESSION_COLLECTOR_2026-06-05_DEPLOY_DCC.md) |

**Keine Secrets** in diesen Dokumenten.

---

## Phase 0 (Session)

- `check-backend-version-gate.sh`: OK
- `check-runtime-profile-deploy-gate.sh`: OK
- Legacy-Gate: exit 20 (Release, erwartet)

---

## Offen (Operator)

- `sudo ./scripts/deploy-to-opt.sh` nur mit Freigabe
- DCC-spezifische Smoke-Tests: interne Sammlung oben
