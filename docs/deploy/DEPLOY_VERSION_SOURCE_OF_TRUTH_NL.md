> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_VERSION_SOURCE_OF_TRUTH_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Version Source of Truth

Central version source: `config/version.json` with `project_version`, `release_stage`, `version_track`.  
alleen-lezen consistency check: `POST /api/Deploy/version-source-of-truth-check` writes `version_source_of_truth_check.json`.
