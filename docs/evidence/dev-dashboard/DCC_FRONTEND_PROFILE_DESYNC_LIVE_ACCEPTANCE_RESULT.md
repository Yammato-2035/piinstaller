# DCC Frontend Profile Desync — Live Acceptance Result

**Datum:** 2026-06-05  
**HEAD vorher:** `5efff70`  
**HEAD nachher:** `4fb72ee` (`Fix DCC frontend profile desync`)  
**Branch:** `main`

## Phase 0 — Known-Error / Roadmap

| Prüfpunkt | Ergebnis |
|-----------|----------|
| Fehler bekannt? | **Ja** — `expected_release_profile_block` vs. Frontend-Gating-Desync dokumentiert in `DCC_PROFILE_AND_PORT_ERRORS.md`, `DCC_FRONTEND_PROFILE_DESYNC_RESULT.md` |
| Frühere Korrektur unvollständig? | **Ja** — Fix war im Workspace, aber **nicht committed** (`HEAD` blieb `5efff70`); **nicht deployed** (`/opt` Frontend-Dist vom 2026-06-04) |
| Portfehler ausgeschlossen? | **Ja** — API `:8000`, UI/DCC `:3001`, nginx `:8080` nicht DCC (`PORTS_AND_PROFILES.md`) |

## Workspace-Fix (gesichert)

- **Commit:** `yes` — `4fb72ee`, 15 Dateien selektiv (kein `git add -A`)
- **Push:** `no`
- **Statische Tests:** `npm --prefix frontend run build` OK; Vitest 58/58 OK; `dccGate.test.ts` (Status 200 → allowed, 404 blocked, stale release + Status 200)

## Deploy nach `/opt`

**Status:** `blocked_by_operator_sudo`

```text
sudo: Ein Passwort ist notwendig
deploy_exit=1
```

**Deploy-Drift (Frontend):**

| Pfad | Workspace | `/opt` |
|------|-----------|--------|
| `frontend/dist/assets/index-*.js` | `index-8mohY8Nk.js` (2026-06-05) | `index-BdkZy7Kg.js` (2026-06-04) |
| `cache:"no-store"` im Bundle | 4 Treffer | 1 Treffer |

Ohne Operator-Deploy läuft `:3001` weiter mit **altem** Produktions-Bundle — Live-Browser-Smoke des neuen Gatings ist **nicht belastbar**.

## Runtime unter `release` (aktuell, erwartet)

| Check | Ergebnis |
|-------|----------|
| `GET /api/version` | HTTP 200 — `install_profile=release`, `dev_control_enabled=false` |
| `GET /api/dev-dashboard/status` | HTTP 404 — `PROFILE_ROUTE_BLOCKED` |
| `GET /api/fleet/sessions` | HTTP 404 — `PROFILE_ROUTE_BLOCKED` |
| `http://127.0.0.1:3001/?window=cockpit` | HTTP 200 (SPA) — Disabled-Page **erwartet** unter release |
| Phase-0-Gate | `check-runtime-profile-deploy-gate.sh` Exit 0 |

## local_lab Live-Acceptance

**Status:** `dcc_profile_switch_blocked` (sudo)

Profilwechsel und Browser-Smoke **nicht ausgeführt**. Erwartung nach Operator-Handoff:

1. Deploy `4fb72ee` nach `/opt`
2. `local_lab` aktivieren
3. `/api/dev-dashboard/status` HTTP 200, Fleet HTTP 200
4. Browser: DCC sichtbar, **keine** release-Disabled-Page
5. `release` restore — Dev-Routen wieder 404

## Ampel (Statusregeln)

| Regel | Status |
|-------|--------|
| Code-Fix ohne Commit | ~~blocked~~ → **erledigt** |
| Commit ohne Deploy | **review_required** |
| Deploy ohne local_lab-Browser-Smoke | ausstehend |
| local_lab + Browser + release restore | **nicht grün** |

**Gesamt:** `yellow` / `review_required` — kein Fake-Green für DCC.

## Operator-Handoff (vollständig)

```bash
cd /home/volker/piinstaller

# 1) Deploy
sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller

curl -sS http://127.0.0.1:8000/api/version | jq '{install_profile, profile_gate_status, dev_control_enabled, backend_runtime_path, runtime_ports, canonical_urls}'
curl -sS -I "http://127.0.0.1:3001/?window=cockpit" | head -10

# 2) local_lab
sudo install -m 0644 packaging/systemd/dropins/92-install-profile-local-lab.conf.example \
  /etc/systemd/system/setuphelfer-backend.service.d/install-profile.conf
sudo systemctl daemon-reload && sudo systemctl restart setuphelfer-backend.service

curl -sS http://127.0.0.1:8000/api/version | jq '{install_profile, profile_gate_status, dev_control_enabled, backend_runtime_path}'
curl -sS -i http://127.0.0.1:8000/api/dev-dashboard/status | head -20
curl -sS -i http://127.0.0.1:8000/api/fleet/sessions | head -20

xdg-open "http://127.0.0.1:3001/?window=cockpit&t=$(date +%s)"

# Browser-Konsole (wenn UI blockiert trotz Status 200):
# await fetch('http://127.0.0.1:8000/api/version', { cache: 'no-store' }).then(r => r.json())
# await fetch('http://127.0.0.1:8000/api/dev-dashboard/status', { cache: 'no-store' }).then(async r => ({ status: r.status, body: await r.text() }))

# 3) release restore (zwingend)
sudo install -m 0644 packaging/systemd/dropins/92-install-profile-release.conf.example \
  /etc/systemd/system/setuphelfer-backend.service.d/install-profile.conf
sudo systemctl daemon-reload && sudo systemctl restart setuphelfer-backend.service

curl -sS http://127.0.0.1:8000/api/version | jq '{install_profile, profile_gate_status, dev_control_enabled}'
curl -sS -i http://127.0.0.1:8000/api/dev-dashboard/status | head -20
```

## Nächster Schritt

Operator führt Deploy + local_lab-Browser-Smoke + release restore aus. Erst danach DCC Frontend Profile Desync auf **grün** setzen. **Keine** Monolith-Aufteilung vor live grünem DCC.
