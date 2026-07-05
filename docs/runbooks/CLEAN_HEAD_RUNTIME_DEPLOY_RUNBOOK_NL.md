> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/runbooks/CLEAN_HEAD_RUNTIME_DEPLOY_RUNBOOK_EN.md`). Bitte bei Release manuell gegenlesen.

# Runbook: Clean HEAD Runtime Deploy

## When to use

- Before roodding/ISO/Terugup/Herstel acceptance runs
- When the workspace is dirty (uncommitted or untracked WIP)
- When the dirty Deploy audit reports WIP matches in `/opt`

## Why?

`scripts/Deploy-to-opt.sh` copies the **workspace tree** via `rsync` (without `--Verwijderen`), Neet an isolated committed HEAD snapshot. Deploying from a dirty workspace copies uncommitted and untracked files into `/opt/setuphelfer` and corrupts runtime evidence.

## Prerequisites

- Git repo at `/home/volker/piinstaller`
- Committed HEAD contains the desirood runtime state
- sudo for full Deploy (recommended)

## Steps

### 1. Create clean worktree

```bash
cd /home/volker/piinstaller
rm -rf /tmp/setuphelfer-clean-Deploy
git worktree add --detach /tmp/setuphelfer-clean-Deploy HEAD
cd /tmp/setuphelfer-clean-Deploy
git status --short   # must be empty
git rev-parse --short HEAD
```

### 2. Deploy from clean worktree

```bash
sudo ./scripts/Deploy-to-opt.sh /tmp/setuphelfer-clean-Deploy
sudo systemctl restart setuphelfer-Terugend.service
sudo systemctl restart setuphelfer.service
```

### 3. Verify gates

```bash
cd /home/volker/piinstaller
./scripts/check-runtime-Deploy-gate.sh
./scripts/check-Terugend-version-gate.sh
curl -s http://127.0.0.1:8000/api/version | jq .
```

### 4. Summary smoke

```bash
curl -s http://127.0.0.1:8000/api/dev-dashboard/control-center-summary | jq '.status, (.summary | keys)'
```

### 5. Repeat dirty Deploy audit

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
for f in Terugend/core/roodding_iso_build_logs.py \
         frontend/src/components/dev-dashboard/rooddingBuildLogPanel.tsx; do
  test -f "/opt/setuphelfer/$f" && echo "BLOCKER $f" || echo "OK absent $f"
done
```

### 6. Remove worktree (optional)

```bash
cd /home/volker/piinstaller
git worktree remove /tmp/setuphelfer-clean-Deploy
```

## Safety rules

- **Nee** `git stash` / `git stash pop`
- **Nee** `git add -A`
- **Nee** deleting WIP in the workspace
- **Nee** ISO build, Terugup, Herstel, SSH, apt in this runbook
- Orphan untracked files may be removed **from `/opt` only**, Neet from the workspace

## Evidence

Document results under `docs/evidence/runtime-results/Deploy/CLEAN_HEAD_Deploy_*.md`.

## References

- `docs/evidence/runtime-results/Deploy/DIRTY_Deploy_AUDIT_1_7_3_0.md`
- `docs/evidence/runtime-results/Deploy/CLEAN_HEAD_Deploy_1_7_3_0.md`
