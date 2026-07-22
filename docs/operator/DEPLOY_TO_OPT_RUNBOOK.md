# Deploy to /opt Runbook

```bash
cd /pfad/zum/sauberen/worktree
./scripts/deploy-to-opt.sh --profile runtime-opt --plan
sudo ./scripts/deploy-to-opt.sh --profile runtime-opt
./scripts/check-runtime-deploy-gate.sh
```

Tauri gehört nicht zum Standard-`runtime-opt`-Deploy.
