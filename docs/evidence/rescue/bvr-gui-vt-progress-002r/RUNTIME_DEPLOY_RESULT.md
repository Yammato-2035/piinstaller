# Runtime Deploy Result – 002R (Resync)

| Feld | Wert |
|------|------|
| Methode | `deploy-to-opt.sh` mit `SETUPHELFER_SKIP_TAURI_BUILD=1` |
| Deployed Commit | `dac7e710` (Impl-Basis `61bac2b3`) |
| Project version | `1.9.20.0` |
| Payload version | `1.10.1.2` |
| Runtime path | `/opt/setuphelfer/backend` |
| Profile gate | green |
| Services | active |
| Tauri | Skip (Binary erhalten), Vite dist neu gebaut |
| Status | **deployed** |

Ursache des vorherigen Abbruchs: unkontrollierter langer `npm run tauri:build`. Fix: Skip-Flag im Deploy-Skript.
