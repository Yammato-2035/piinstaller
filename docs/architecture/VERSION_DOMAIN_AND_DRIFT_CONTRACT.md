# Version Domains and Drift Contract

## Domains

- **application_runtime:** `config/version.json` / `/api/version` / `/opt`
- **source_commit:** Workspace HEAD (falls vorhanden) / Deploy-Manifest `source.commit` / Runtime-Manifest
- **rescue_payload:** `config/rescue_payload_version.json` / USB / physischer Run
- **packaging:** deb/rpm Artefakte

## Nicht vergleichen

`application_runtime` (z. B. 1.9.20.x) **nicht** direkt gegen `rescue_payload` (z. B. 1.10.1.x).

## RUNTIME_API

Ohne lokalen Git-Workspace: Deploy-Quellcommit aus Manifest; fehlender Workspace-HEAD ist kein automatischer Rot-Blocker.
