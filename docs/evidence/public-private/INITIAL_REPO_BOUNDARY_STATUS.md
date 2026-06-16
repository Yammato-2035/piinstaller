# Initial Repository Boundary Status

**Erstellt:** 2026-06-16  
**Auftrag:** Public/Private Boundary, Monolith-Entkopplung, Telemetrie-Vorbereitung (kein Deploy)

## Repository-Kontext

| Feld | Wert |
|------|------|
| Branch | `main` |
| HEAD | `86ee180` |
| Remote fetch | `https://github.com/Yammato-2035/piinstaller.git` |
| Remote push | `https://github.com/Yammato-2035/piinstaller.git` |
| GitHub-Sichtbarkeit | **PUBLIC** (`gh repo view`: `visibility=PUBLIC`) |

## Gate-Status (Phase 0)

| Gate | Ergebnis | Exit |
|------|----------|------|
| `check-runtime-deploy-gate.sh` | LEGACY_GATE_NON_PROFILE_AWARE — `/api/dev-dashboard/status` HTTP 404; Profil-Gate-Hinweis | 20 |
| `check-backend-version-gate.sh` | OK (HTTP 200, Versionsfelder, config konsistent) | 0 |
| `check-module-boundaries.sh` | `review_required` (app.py 15142 Zeilen, Duplikat-Hinweise) | 0 |

## Dirty Tree

- Modifiziert: `ckb-next` (Submodul)
- Viele untracked `docs/evidence/*` (Runtime-/Rescue-Evidence, nicht Teil dieses Auftrags)
- **Neue Dateien dieses Auftrags:** noch nicht committed

## Erkannte sensible Dateinamen (ohne Inhalt)

| Pfad | Hinweis |
|------|---------|
| `./.env` | Lokale Umgebung — **nicht committen** |
| `./scripts/tests/test_rescue_network_menu_no_secret_logging_v1.sh` | Testskript (Name enthält „secret“) |

Keine `*.pem`, `*.key`, `*.p12`, `*.pfx` im Workspace-Root (maxdepth 5).

## Entscheidung

| Kriterium | Wert |
|-----------|------|
| `public_repo_context` | **ja** — GitHub visibility PUBLIC |
| `private_repo_context` | nein |
| `unknown_context` | nein |

## Zulässiger Arbeitsmodus

**`public_safe_docs_and_contracts_only`**

- Kein proprietärer Cloudserver-Code erstellen
- Kein echter Telemetrie-Server-Code erstellen
- Kein Operator-Dashboard-Code erstellen
- Nur public-safe Doku, Contracts, Stubs, Boundary-Gates, Handoff-Dateien
- Kein produktiver Deploy

## Explizite Nicht-Aktionen

- Kein Live-Deploy
- Kein Plesk-Live-Deploy
- Kein Upload privater Implementierung nach Public GitHub
- Keine kostenlose Plesk-Version bauen
