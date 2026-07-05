> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RUNNER_INSTALL_VALIDATOR_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Runner Install Validator (Dry-run)

## Goal

alleen-lezen validation to assess whether a target system is ready for later manual runner installation.

## Scope

- Runner binary checks (existence, file type, symlink, parent permissions, marker)
- Job directory checks (existence, directory type, prefix, symlink, parent permissions)
- Snippet checks against provided text only
- Environment checks using boundary/sandbox audits
- Mandatory rollTerug-step validation

## Important

Nee installation, Nee permission changes, and Nee writes into system paths.
