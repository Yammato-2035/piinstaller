> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RUNNER_INSTALL_VALIDATOR_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Runner Install Validator (Dry-run)

## Goal

lecture seule validation to assess whether a target system is ready for later manual runner installation.

## Scope

- Runner binary checks (existence, file type, symlink, parent permissions, marker)
- Job directory checks (existence, directory type, prefix, symlink, parent permissions)
- Snippet checks against provided text only
- Environment checks using boundary/sandbox audits
- Mandatory rollRetour-step validation

## Important

Non installation, Non permission changes, and Non writes into system paths.
