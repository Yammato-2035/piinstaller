# Deploy Version Source of Truth

Zentrale Versionsquelle: `config/version.json` mit `project_version`, `release_stage`, `version_track`.  
Read-only Konsistenzcheck: `POST /api/deploy/version-source-of-truth-check` schreibt `version_source_of_truth_check.json`.
