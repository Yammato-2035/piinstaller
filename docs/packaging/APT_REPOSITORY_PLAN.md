# APT repository plan (packaging)

## Goal

Deliver Setuphelfer updates to installed systems via **APT** with verifiable versions and safe service restarts.

## Components

- **Pool / dist**: repository layout (`conf/distributions`, `includedeb`, etc.) or hosted equivalent.
- **Signing**: `Release` + `InRelease` signatures; optionally per-`.deb` signing.
- **CI publish**: upload artefacts from tagged releases only (policy TBD).
- **Client pin**: optional APT pinning file for staged rollouts.

## Relation to version gate

Until the repository exists, operators rely on **`scripts/check-backend-version-gate.sh`** and manual `/opt` updates per **`docs/operations/BACKEND_UPDATE_RUNBOOK_*.md`**.

## Open decisions

- Hosting (self-hosted vs. cloud object storage + CDN).
- Support matrix (Debian/Ubuntu versions).
- Coexistence with legacy `pi-installer` package names (if any).
