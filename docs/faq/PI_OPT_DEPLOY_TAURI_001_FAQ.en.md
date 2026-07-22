# FAQ Deploy/Tauri (en-US)

1. Warum baut der /opt-Deploy kein Tauri? → Profil runtime-opt benötigt es nicht.
2. Wann Tauri? → desktop-development / desktop-release / --with-tauri.
3. Was ist runtime-opt? → Backend + Web nach /opt ohne Desktop-Binary.
4. Web vs Tauri? → Vite-dist im Browserdienst vs. native Desktop-App.
5. RUNTIME_API ohne Workspace-HEAD? → normal; Manifest-Commit zählt.
6. Deploy-Quellcommit? → Deploy-Manifest `source.commit`.
7. Deploy-Drift? → Runtime vs Manifest/Commit, nicht App vs Payload.
8. 1.9.20.x vs Payload 1.10.1.x? → getrennte Domänen, erlaubt.
9. Wann deployed? → Deploy Exit 0 + Manifest + Gate grün.
10. blocked_runtime_outdated? → Runtime älter/abweichend von App-Version, nicht fehlendes Git.
