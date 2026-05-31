# Runbook: Clean HEAD Runtime Deploy

## When to use

- Before rescue/ISO/backup/restore acceptance runs
- When the workspace is dirty (uncommitted or untracked WIP)
- When the dirty deploy audit reports WIP matches in `/opt`

## Why?

`scripts/deploy-to-opt.sh` copies the **workspace tree** via `rsync` (without `--delete`), not an isolated committed HEAD snapshot. Deploying from a dirty workspace copies uncommitted and untracked files into `/opt/setuphelfer` and corrupts runtime evidence.

## Prerequisites

- Git repo at `/home/volker/piinstaller`
- Committed HEAD contains the desired runtime state
- sudo for full deploy (recommended)

## Steps

### 1. Create clean worktree

```bash
cd /home/volker/piinstaller
rm -rf /tmp/setuphelfer-clean-deploy
git worktree add --detach /tmp/setuphelfer-clean-deploy HEAD
cd /tmp/setuphelfer-clean-deploy
git status --short   # must be empty
git rev-parse --short HEAD
```

### 2. Deploy from clean worktree

```bash
sudo ./scripts/deploy-to-opt.sh /tmp/setuphelfer-clean-deploy
sudo systemctl restart setuphelfer-backend.service
sudo systemctl restart setuphelfer.service
```

### 3. Verify gates

```bash
cd /home/volker/piinstaller
./scripts/check-runtime-deploy-gate.sh
./scripts/check-backend-version-gate.sh
curl -s http://127.0.0.1:8000/api/version | jq .
```

### 4. Summary smoke

```bash
curl -s http://127.0.0.1:8000/api/dev-dashboard/control-center-summary | jq '.status, (.summary | keys)'
```

### 5. Repeat dirty deploy audit

```bash
cd /home/volker/piinstaller
git diff --name-only > /tmp/setuphelfer_dirty_files.txt
: > /tmp/setuphelfer_dirty_runtime_matches.txt
while read -r f; do
  if [ -f "$f" ] && [ -f "/opt/setuphelfer/$f" ]; then
    ws="$(sha256sum "$f" | awk '{print $1}')"
    rt="$(sha256sum "/opt/setuphelfer/$f" | awk '{print $1}')"
    [ "$ws" = "$rt" ] && echo "MATCH $f" >> /tmp/setuphelfer_dirty_runtime_matches.txt
  fi
done < /tmp/setuphelfer_dirty_files.txt
cat /tmp/setuphelfer_dirty_runtime_matches.txt   # must be empty
```

Critical untracked files must be **absent** in `/opt`:

```bash
for f in backend/core/rescue_iso_build_logs.py \
         frontend/src/components/dev-dashboard/RescueBuildLogPanel.tsx; do
  test -f "/opt/setuphelfer/$f" && echo "BLOCKER $f" || echo "OK absent $f"
done
```

### 6. Remove worktree (optional)

```bash
cd /home/volker/piinstaller
git worktree remove /tmp/setuphelfer-clean-deploy
```

## Safety rules

- **No** `git stash` / `git stash pop`
- **No** `git add -A`
- **No** deleting WIP in the workspace
- **No** ISO build, backup, restore, SSH, apt in this runbook
- Orphan untracked files may be removed **from `/opt` only**, not from the workspace

## Evidence

Document results under `docs/evidence/runtime-results/deploy/CLEAN_HEAD_DEPLOY_*.md`.

## References

- `docs/evidence/runtime-results/deploy/DIRTY_DEPLOY_AUDIT_1_7_3_0.md`
- `docs/evidence/runtime-results/deploy/CLEAN_HEAD_DEPLOY_1_7_3_0.md`
