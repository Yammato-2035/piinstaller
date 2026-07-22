# PI-OPT-DEPLOY-TAURI-001 – Abschlussbericht

## 1. Workspace und Git
- Worktree: `/tmp/piinstaller-opt-deploy-tauri-001`
- Branch: `pi-opt-deploy-tauri-001` → `origin/pi-opt-deploy-tauri-001`
- HEAD: `7e80319000c0`
- fremde Drift: unberührt

## 2. Root Cause
- `npm run tauri:build` lief in `deploy-to-opt.sh` immer bei verfügbarem Cargo
- /opt-Services brauchen nur Vite-dist + Backend

## 3–6. Fix
- Profil `runtime-opt` (Default) ohne Tauri
- `--plan` / `--with-tauri` / `--skip-tauri`
- Manifest mit `source.commit`, App vs Payload getrennt
- RUNTIME_API: kein Auto-Rot wegen fehlendem Workspace-HEAD
- Legacy-Gate → Profile-Gate ohne Rekursion
- Version **1.9.20.1** (Payload **1.10.1.2** unverändert)

## 8–10. Deploy / Runtime / Gate
- Deploy Exit 0, Tauri nicht ausgeführt
- Runtime 1.9.20.1, Gate Exit 0
- Rescue-Status weiterhin lesbar

## 13. Endstatus
**passed**
