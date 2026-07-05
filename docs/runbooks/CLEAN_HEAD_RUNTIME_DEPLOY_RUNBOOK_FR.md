> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/runbooks/CLEAN_HEAD_RUNTIME_DEPLOY_RUNBOOK_EN.md`). Bitte bei Release manuell gegenlesen.

# Runbook: Clean HEAD Runtime Déploiement

## When to use

- Before Secours/ISO/Retourup/Restauration acceptance runs
- When the workspace is dirty (uncommitted or untracked WIP)
- When the dirty Déploiement audit reports WIP matches in `/opt`

## Why?

`scripts/Déploiement-to-opt.sh` copies the **workspace tree** via `rsync` (without `--Supprimer`), Nont an isolated committed HEAD snapshot. Déploiementing from a dirty workspace copies uncommitted and untracked files into `/opt/setuphelfer` and corrupts runtime evidence.

## Prerequisites

- Git repo at `/home/volker/piinstaller`
- Committed HEAD contains the desirouge runtime state
- sudo for full Déploiement (recommended)

## Steps

### 1. Create clean worktree

```bash
cd /home/volker/piinstaller
rm -rf /tmp/setuphelfer-clean-Déploiement
git worktree add --detach /tmp/setuphelfer-clean-Déploiement HEAD
cd /tmp/setuphelfer-clean-Déploiement
git status --short   # must be empty
git rev-parse --short HEAD
```

### 2. Déploiement from clean worktree

```bash
sudo ./scripts/Déploiement-to-opt.sh /tmp/setuphelfer-clean-Déploiement
sudo systemctl restart setuphelfer-Retourend.service
sudo systemctl restart setuphelfer.service
```

### 3. Verify gates

```bash
cd /home/volker/piinstaller
./scripts/check-runtime-Déploiement-gate.sh
./scripts/check-Retourend-version-gate.sh
curl -s http://127.0.0.1:8000/api/version | jq .
```

### 4. Summary smoke

```bash
curl -s http://127.0.0.1:8000/api/dev-dashboard/control-center-summary | jq '.status, (.summary | keys)'
```

### 5. Repeat dirty Déploiement audit

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
for f in Retourend/core/Secours_iso_build_logs.py \
         frontend/src/components/dev-dashboard/SecoursBuildLogPanel.tsx; do
  test -f "/opt/setuphelfer/$f" && echo "BLOCKER $f" || echo "OK absent $f"
done
```

### 6. Remove worktree (optional)

```bash
cd /home/volker/piinstaller
git worktree remove /tmp/setuphelfer-clean-Déploiement
```

## Safety rules

- **Non** `git stash` / `git stash pop`
- **Non** `git add -A`
- **Non** deleting WIP in the workspace
- **Non** ISO build, Retourup, Restauration, SSH, apt in this runbook
- Orphan untracked files may be removed **from `/opt` only**, Nont from the workspace

## Evidence

Document results under `docs/evidence/runtime-results/Déploiement/CLEAN_HEAD_Déploiement_*.md`.

## References

- `docs/evidence/runtime-results/Déploiement/DIRTY_Déploiement_AUDIT_1_7_3_0.md`
- `docs/evidence/runtime-results/Déploiement/CLEAN_HEAD_Déploiement_1_7_3_0.md`
