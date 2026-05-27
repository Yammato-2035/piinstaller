# Development Dashboard & Control Center

Setuphelfer bietet zwei eng verzahnte Oberflächen für Entwickler:

| Oberfläche | Zweck | Einstieg |
|----------|--------|---------|
| **Development Cockpit** (inline) | Modulboard, Roadmap, Detail-Panels | `?page=dev-dashboard` oder Sidebar (Browser-Fallback) |
| **Governance Cockpit** (`CockpitApp`) | Governance-Matrix, Roadmap-Registry (ab 2026-05-27), Gate-Panels | Separater Build/Einstieg — Roadmap erst nach Frontend-Deploy live unter `/opt` |
| **Development Control Center** (extern) | Live-Governance, 16-Bereiche-Matrix, Timeline | Tauri-Fenster `cockpit` oder `?window=cockpit` |

## Runtime vs. Standalone

- **Runtime-API** (`source=runtime_api`): Backend unter `/opt/setuphelfer`, Endpunkte `/api/dev-dashboard/*`. Gates und Drift beziehen sich auf die produktive Installation.
- **Standalone** (API offline): Workspace-Scan (Tauri) oder Snapshot (`frontend/public/dev-dashboard.snapshot.json`). **Safe Test Mode bleibt LOCKED** — keine Runtime-Tests, kein Backup/Restore.

## Roadmap-Registry

- `docs/roadmap/setuphelfer_roadmap.json`, `setuphelfer_next_prompts.json`
- `TERMINAL_A_READONLY` = **completed** (2026-05-27)
- Phase-0-Gate: Exit **0** (`deploy_drift` green, `safe_test_mode` UNLOCKED) — Stand 2026-05-27
- Nächster Prompt: **RESCUE_ISO_MANUAL_OPERATOR_TERMINAL_BUILD**

## Manuelle Kommandoläufe (read-only)

- Evidence: `docs/evidence/dev-dashboard/manual_command_runs/*.json`
- API: `GET /api/dev-dashboard/manual-command-runs`
- UI: Developer Dashboard → **Struktur** → Panel „Manuelle Kommandoläufe“
- **Keine** Shell-Ausführung aus dem Dashboard

## Dev-Server (Vite) vs. Produktion

Der **Vite-Port ist dynamisch** — nicht fest **5173** für das Browser-Cockpit.

| Modus | Standard-Port | Hinweis |
|-------|---------------|---------|
| `npm run dev:cockpit` | **3001** (`vite.config.ts`) | Wenn 3001 belegt ist, weicht Vite z. B. auf **3002** aus — Port im Terminal lesen |
| `npm run dev:tauri` / Tauri | **5173** (`--strictPort`) | Nur wenn dieser Dev-Server läuft |
| Produktion | Backend **8000** | `frontend/dist` unter `/opt/setuphelfer` |

**Beispiel (aktuell lokal):** `http://127.0.0.1:3002/?window=cockpit`  
**Backend-API:** `http://127.0.0.1:8000`

Falsch als feste Annahme: `http://127.0.0.1:5173/?window=cockpit` ohne laufenden Tauri/Vite auf 5173.

## Phase-0-Gate (Pflicht vor Runtime-Arbeit)

```bash
./scripts/check-runtime-deploy-gate.sh   # Exit 0
```

Voraussetzungen u. a.: `setuphelfer-backend.service` aktiv, `/api/version` HTTP 200, `project_version` = `config/version.json`, `deploy_drift` nicht blockierend, `backend_runtime_path` = `/opt/setuphelfer/backend`.

### Workspace-Zugriff (Development-Drop-in)

Das Development Cockpit und `deploy_drift` brauchen **lesenden** Zugriff auf den Workspace-Checkout (z. B. unter `/home/.../piinstaller`), während die API aus `/opt/setuphelfer` läuft.

- **Root Cause:** `ProtectHome=yes` in der Basis-Unit blockiert `/home` so, dass weder `Path.is_file()` noch `os.stat` auf den Checkout zugreifen — auch mit `ReadOnlyPaths` auf den Workspace-Pfad (systemd: `EACCES`).
- **Developer-Drop-in only:** `scripts/write-dev-workspace-systemd-dropin.sh` setzt **`ProtectHome=read-only`** (nur für Maschinen mit `SETUPHELFER_DEV_WORKSPACE_ROOT`). Die Release-/Endnutzer-Härtung der Haupt-Unit (`ProtectHome=yes`) wird **nicht** pauschal abgesenkt.
- **Gate bleibt read-only:** Deploy-Drift vergleicht Hashes/Manifeste; es gibt keinen Schreibzugriff auf den Workspace und keine automatischen Deploy-Aktionen aus dem Cockpit.

```bash
sudo ./scripts/write-dev-workspace-systemd-dropin.sh
sudo systemctl daemon-reload
sudo systemctl restart setuphelfer-backend.service
```

Prüfung: `runtime_gate.passed` true und `deploy_drift.status` green in `/api/dev-dashboard/status`.

## Deploy nach /opt

```bash
sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller
sudo systemctl restart setuphelfer-backend.service
```

Manifest erzeugen (Workspace):

```bash
python3 backend/tools/generate_deploy_manifest.py
```

## Control Center starten

```bash
cd frontend
npm run tauri:dev-cockpit      # Tauri + Backend (empfohlen)
npm run dev:cockpit             # nur Browser: ?window=cockpit
npm run tauri:dev-standalone    # ohne Backend-Zwang
```

In der Haupt-App (Tauri): Sidebar **„Control Center (extern)“** → `open_development_cockpit`.

## Governance (kurz)

- **Matrix**: 16 Bereiche (runtime, backup, evidence, …) — Ampeln aus API/Modulen, kein Fake-Grün.
- **Timeline**: lokale Historie (`localStorage`), echte Übergänge (grün/regression/api on/off).
- **Prompt-Export**: Meta-Prompt mit Blockern, Work Order, Modulzuständen.

Weitere Sprachen: [EXTERNAL_CONTROL_CENTER_DE.md](./EXTERNAL_CONTROL_CENTER_DE.md), [EXTERNAL_CONTROL_CENTER_EN.md](./EXTERNAL_CONTROL_CENTER_EN.md).
