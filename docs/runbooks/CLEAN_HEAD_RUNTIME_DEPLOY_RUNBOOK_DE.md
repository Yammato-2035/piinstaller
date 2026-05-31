# Runbook: Clean HEAD Runtime Deploy

## Wann verwenden?

- Vor Rescue-/ISO-/Backup-/Restore-Abnahmen
- Wenn der Workspace dirty ist (uncommitted oder untracked WIP)
- Wenn der Dirty-Deploy-Audit WIP-Matches in `/opt` meldet

## Warum?

`scripts/deploy-to-opt.sh` kopiert den **Workspace-Baum** per `rsync` (ohne `--delete`), nicht isoliert committed HEAD. Ein Deploy aus einem dirty Workspace überträgt uncommitted und untracked Dateien nach `/opt/setuphelfer` und verfälscht Runtime-Evidence.

## Voraussetzungen

- Git-Repo unter `/home/volker/piinstaller`
- Committed HEAD enthält den gewünschten Runtime-Stand
- sudo für vollständigen Deploy (empfohlen)

## Schritte

### 1. Clean Worktree erzeugen

```bash
cd /home/volker/piinstaller
rm -rf /tmp/setuphelfer-clean-deploy
git worktree add --detach /tmp/setuphelfer-clean-deploy HEAD
cd /tmp/setuphelfer-clean-deploy
git status --short   # muss leer sein
git rev-parse --short HEAD
```

### 2. Deploy aus clean Worktree

```bash
sudo ./scripts/deploy-to-opt.sh /tmp/setuphelfer-clean-deploy
sudo systemctl restart setuphelfer-backend.service
sudo systemctl restart setuphelfer.service
```

### 3. Gates prüfen

```bash
cd /home/volker/piinstaller
./scripts/check-runtime-deploy-gate.sh
./scripts/check-backend-version-gate.sh
curl -s http://127.0.0.1:8000/api/version | jq .
```

### 4. Summary-Smoke

```bash
curl -s http://127.0.0.1:8000/api/dev-dashboard/control-center-summary | jq '.status, (.summary | keys)'
```

### 5. Dirty Deploy Audit wiederholen

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
cat /tmp/setuphelfer_dirty_runtime_matches.txt   # muss leer sein
```

Kritische untracked Dateien müssen in `/opt` **absent** sein:

```bash
for f in backend/core/rescue_iso_build_logs.py \
         frontend/src/components/dev-dashboard/RescueBuildLogPanel.tsx; do
  test -f "/opt/setuphelfer/$f" && echo "BLOCKER $f" || echo "OK absent $f"
done
```

### 6. Worktree aufräumen (optional)

```bash
cd /home/volker/piinstaller
git worktree remove /tmp/setuphelfer-clean-deploy
```

## Sicherheitsregeln

- **Kein** `git stash` / `git stash pop`
- **Kein** `git add -A`
- **Kein** Löschen von WIP im Workspace
- **Kein** ISO-Build, Backup, Restore, SSH, apt in diesem Runbook
- Orphan untracked Dateien dürfen **nur aus `/opt`** entfernt werden, nicht aus dem Workspace

## Evidence

Ergebnis dokumentieren unter `docs/evidence/runtime-results/deploy/CLEAN_HEAD_DEPLOY_*.md`.

## Referenz

- `docs/evidence/runtime-results/deploy/DIRTY_DEPLOY_AUDIT_1_7_3_0.md`
- `docs/evidence/runtime-results/deploy/CLEAN_HEAD_DEPLOY_1_7_3_0.md`
