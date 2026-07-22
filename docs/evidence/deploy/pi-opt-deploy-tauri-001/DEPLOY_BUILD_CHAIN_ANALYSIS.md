# Deploy Build Chain Analysis – PI-OPT-DEPLOY-TAURI-001

## Antworten

1. **Tauri-Befehl:** `npm run tauri:build` (ggf. via `su - $SUDO_USER`).
2. **Skript:** `scripts/deploy-to-opt.sh` nach Vite-`npm run build`.
3. **Bisher:** immer, sobald Cargo verfügbar und `SETUPHELFER_SKIP_TAURI_BUILD` nicht gesetzt.
4. **Webfrontend:** ja (`frontend/dist`, `setuphelfer.service`).
5. **Tauri nach /opt:** Binary bleibt unter `frontend/src-tauri/target` (rsync schließt `target/` aus); kein systemd-Dienst startet Tauri.
6. **/opt-Services:** `setuphelfer-backend`, `setuphelfer` (Python HTTP + Vite-dist) — kein Tauri.
7. **Historisch:** Desktop-Packaging-Pfad in Runtime-Deploy übernommen.
8. **Flags vorher:** nur `SETUPHELFER_SKIP_TAURI_BUILD=1`; jetzt `--profile runtime-opt`, `--plan`, `--with-tauri`, `--skip-tauri`.
9. **Hängen:** vollständiger Cargo/Tauri-Release (Minuten).
10. **Art:** echter Build, nicht nur Lock.
11. **/opt braucht:** Backend, config, Vite-dist, systemd, Deploy-Manifest — nicht Tauri.

Confidence: **high**
