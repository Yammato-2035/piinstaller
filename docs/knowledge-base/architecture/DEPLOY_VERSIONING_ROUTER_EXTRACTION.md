# Versioning-Router (D.10) — Kurzüberblick

8 plan-only POST-Routen in `routes_versioning.py` (Identifier-Migration, Safe-Rewrite-**Plan**, Elimination-Targets/Plan, Compatibility-Validation, Patch-Bump-Preparation, Legacy-Migration-Matrix).

- Keine Runner-Ausführung
- `allowed_to_execute` = false
- Pfade unverändert unter `/api/deploy/...`

Details: `docs/architecture/DEPLOY_VERSIONING_ROUTER_EXTRACTION_D10.md`
