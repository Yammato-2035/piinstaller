# Rescue Developer ISO Build — Permission Analysis

Run-ID (failed build): `rescue_developer_iso_20260531_100050`
Generated: 2026-05-31 (analysis phase, pre-fix)

## Exact error

During `lb config noauto` in the controlled build:

```
touch: '.build/config' kann nicht berührt werden: Keine Berechtigung
```

Build log: `build/rescue/logs/controlled-iso-build/latest.log`

## BUILD_TREE ownership

| Path | Owner | Writable by operator (gabriel) |
|------|-------|----------------------------------|
| `build/rescue/live-build/setuphelfer-rescue-live` | gabriel:workspace | yes |
| `.build/` | root:workspace | **no** |
| `.build/config` | root:workspace (644) | **no** |
| `config/` | gabriel:workspace | yes |
| `auto/` | gabriel:workspace | yes |

## Root-owned artifacts

At least **40+** root-owned paths under the build tree (sample in `/tmp/setuphelfer_rescue_live_build_root_owned_before.txt`), including:

- Entire `.build/` directory and all stage marker files
- Top-level `binary.contents`, `binary.packages`
- Top-level `chroot.headers`, `chroot.packages.*`
- Multiple `wget-log*` files from prior builds

## `.build/config`

- **Exists:** yes (empty file, mode 644, root:workspace)
- **Writable by operator:** no

## Tree writability

- Build tree root: **writable**
- `.build`: **not writable** — blocks `lb config` (`touch .build/config`)

## Prior artifacts involved

Yes. A previous `sudo lb build` left root-owned live-build state. Operator removed `binary`, `chroot`, `cache`, `local` with sudo but **did not remove `.build/`** or root-owned top-level `binary.*` / `chroot.*` / `wget-log*` files.

## Root cause

Mixed ownership: user-owned `config/` and `auto/` coexist with root-owned `.build/` from an earlier sudo build. `./auto/config` invokes `lb config`, which tries to update `.build/config` as the operator user and fails.

## Repair status

**Not repaired in this document.** Fix is implemented via permission policy, preflight guard, and `clean-controlled-live-build-tree.sh` (operator-run).

See: `docs/architecture/RESCUE_CONTROLLED_ISO_BUILD_PERMISSION_POLICY.md`
