# Post-Deploy / Script-Sync 55b7bce

**Stand:** 2026-06-02

| Aktion | Ergebnis |
|--------|----------|
| `deploy-to-opt.sh` (vollständig) | **nein** (`sudo` Passwort erforderlich) |
| Script-Sync nach `/opt` | **ja** — `fleet-session-api.sh` aus Worktree `55b7bce` kopiert (Datei für User `gabriel` schreibbar) |
| Backend-Restart | **nein** (nur Shell-Skript; Backend unverändert) |
| `/opt` enthält `${3-}` Fix | **yes** |
| `setuphelfer-backend.service` | **active** |
| Profil nach Sync | `local_lab` |
| Profil-Gate | Exit **0** |
| Legacy Deploy-Gate | Exit **0** |

Hinweis: Vollständiger `deploy-to-opt` aus Worktree bleibt für Operator empfohlen, wenn auch Backend/Frontend auf `55b7bce` gezogen werden sollen.
