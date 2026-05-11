# Deploy Version Source of Truth

Central version source: `config/version.json` with `project_version`, `release_stage`, `version_track`.  
Read-only consistency check: `POST /api/deploy/version-source-of-truth-check` writes `version_source_of_truth_check.json`.
