# Deploy Runner Install Validator (Dry-run)

## Goal

Read-only validation to assess whether a target system is ready for later manual runner installation.

## Scope

- Runner binary checks (existence, file type, symlink, parent permissions, marker)
- Job directory checks (existence, directory type, prefix, symlink, parent permissions)
- Snippet checks against provided text only
- Environment checks using boundary/sandbox audits
- Mandatory rollback-step validation

## Important

No installation, no permission changes, and no writes into system paths.
