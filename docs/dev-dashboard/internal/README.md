# Interne Sammlung — Developer Cockpit & Dev-Server

**Nicht für öffentliche FAQ oder allgemeine Wissensdatenbank bestimmt.**

Dieser Ordner bündelt operator- und entwicklungsspezifische Notizen zu:

- Development Control Center (DCC)
- Developer Capability / Token-Gates (ohne Secret-Werte)
- Dev-Server-Ports und profilabhängige Routen
- Live-Acceptance-Schritte nach Deploy

**Regeln:**

1. **Keine Secrets** in Dateien dieses Ordners (keine Token-Werte, keine Passwörter, keine privaten Pfade mit Credentials).
2. Verweise auf Token nur als **Umgebungsvariable oder Dateipfad-Muster** (z. B. „Token aus lokaler Operator-Datei“).
3. Öffentliche KB/FAQ verlinken hierher **nicht** — umgekehrt verweisen interne Notizen auf öffentliche Deploy-Doku.

| Datei | Inhalt |
|-------|--------|
| [SESSION_COLLECTOR_2026-06-05_DEPLOY_DCC.md](./SESSION_COLLECTOR_2026-06-05_DEPLOY_DCC.md) | Deploy-Fix + DCC compact-status, Capability, Gates |

Allgemeiner Deploy nach `/opt`: [DEPLOY_TO_OPT_RUNTIME_SYNC.md](../../knowledge-base/deploy/DEPLOY_TO_OPT_RUNTIME_SYNC.md)
