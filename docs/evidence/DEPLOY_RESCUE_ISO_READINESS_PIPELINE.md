# Evidence — Deploy Rescue ISO readiness pipeline

## Nachweisziel

Nachvollziehbare JSON-Handoffs, API-Codes `DEPLOY_RESCUE_*` und Tests in `backend/tests/test_deploy_runner_rescue_iso_readiness_pipeline_v1.py` ohne ISO-Binary-Erzeugung.

## Artefakte

| Komponente | Datei |
|------------|--------|
| Runner | `backend/deploy/runner_rescue_iso_readiness_pipeline.py` |
| Routen | `backend/deploy/routes.py` (`/rescue/iso-*`, `offline-runtime-validation`, `bootflow-simulation`) |
