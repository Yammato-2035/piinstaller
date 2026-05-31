# Rescue Controlled ISO Build — Permission Policy

Version: 1.7.3.0
Decision: **Variant A** — user-owned preparation/config; controlled sudo only for live-build phases that require root.

## Problem

A prior `sudo lb build` left root-owned artifacts under `.build/`, `binary.*`, and `chroot.*`. A later operator build reached `lb config` as a normal user and failed with:

```
touch: '.build/config' kann nicht berührt werden: Keine Berechtigung
```

Partial cleanup (`sudo rm -rf binary chroot cache local`) did not remove `.build/`.

## Policy rules

1. **No build from a mixed-ownership tree.** Before `lb config`, the working tree must be consistently writable by the operator user, or absent.
2. **Ownership preflight is mandatory.** Preflight and the build entrypoint check permissions before `./auto/config`.
3. **Active work areas** (`.build`, `binary`, `chroot`, `cache`, `local`) must either be missing or user-writable. Root-owned entries block the build.
4. **Controlled clean.** Old root-owned artifacts may be removed only by `scripts/rescue-live/clean-controlled-live-build-tree.sh` with explicit operator confirmation.
5. **Agent/dashboard runs** must not start a real build without operator policy. No hidden sudo escalation from agent context.
6. **Operator terminal** may use sudo deliberately for clean and for `lb build`, documented in run logs.

## Allowed clean targets

Under `build/rescue/live-build/setuphelfer-rescue-live` only:

- `.build/`
- `binary/`, `chroot/`, `cache/`, `local/`
- Top-level `binary.*`, `chroot.*`, `wget-log*`

## Blocker codes

| Code | Meaning |
|------|---------|
| `rescue_iso_build.permission_denied_dot_build` | `.build` or permission preflight blocked |
| Exit 34 | Build script permission preflight blocked (no `lb config`) |

## Operator fix workflow

```bash
./scripts/rescue-live/clean-controlled-live-build-tree.sh --dry-run
sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
./scripts/rescue-live/preflight-developer-controlled-iso-build.sh "$RUN_ID"
```

Preflight must show `permission_policy.operator_fix_required=false` before build.
