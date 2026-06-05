# DCC Live Acceptance — After Fallback Deploy (Operator Observation)

**Datum:** 2026-06-05  
**HEAD:** `199d3c6`  
**Lauf-Typ:** Ingest / Acceptance (keine Reparatur)

## Operator-Sichtbefund (manuell)

| Befund | Status |
|--------|--------|
| DCC wird angezeigt | **ja** |
| Boot-/Fallback-Diagnoseanzeige sichtbar | **ja** |
| Früherer Zustand „Browser leer / DCC zeigt nichts“ | **nicht mehr aktueller Fehlerzustand** |

## Bundle-/Serve-Nachweis (read-only)

| Prüfung | Ergebnis |
|---------|----------|
| `/opt` Marker | `DCC_BOOT_DIAGNOSTICS_V1`, `dcc-boot-diagnostics`, `dcc-cockpit-shell`, `dev-control-disabled`, `PROFILE_ROUTE_BLOCKED` |
| Served Asset | `assets/index-FgGYQFBB.js` |
| Served Marker | identisch zu `/opt` |

**`stale_or_wrong_bundle`:** widerlegt für diesen Stand.

## API-Wahrheit (read-only)

| Feld | Wert |
|------|------|
| `install_profile` | `local_lab` |
| `dev_control_enabled` | `true` |
| `profile_gate_status` | `green` |
| `backend_runtime_path` | `/opt/setuphelfer/backend` |
| `/api/dev-dashboard/status` | HTTP **200** |
| `/api/fleet/sessions` | HTTP **200** |
| `/api/dev-dashboard/recent-evidence` | HTTP **200** |
| UI `:3001/?window=cockpit` | HTTP **200** |

Portlage: API `:8000`, DCC `:3001`, nginx `:8080` nicht DCC — **kein Portfehler**.

## Klassifikation

```text
status=partial_green
classification=dcc_live_visible_after_deploy
blank_dcc_screen=resolved
frontend_gating_desync=not_primary_cause_for_this_stand
```

**Nicht voll grün**, weil **release restore** nach local_lab-Smoke in diesem Ingest-Lauf noch nicht dokumentiert ist (Pflicht für `green` laut Statusregeln).

## Known-Error-Auflösung

| ID | Stand |
|----|-------|
| `blank_dcc_screen` | **resolved** (Bundle + Operator-Sicht + Fail-safe UI) |
| `stale_or_wrong_bundle` | **widerlegt** |
| `frontend_gating_desync` | **nicht Primärursache** (DCC/Fallback sichtbar unter local_lab + Status 200) |

## Verbleibender Operator-Schritt (für `green`)

```bash
sudo install -m 0644 packaging/systemd/dropins/92-install-profile-release.conf.example \
  /etc/systemd/system/setuphelfer-backend.service.d/install-profile.conf
sudo systemctl daemon-reload && sudo systemctl restart setuphelfer-backend.service

curl -sS http://127.0.0.1:8000/api/version | jq '{install_profile, dev_control_enabled}'
curl -sS -i http://127.0.0.1:8000/api/dev-dashboard/status | head -15
# Erwartung: release, dev_control_enabled=false, Status 404 PROFILE_ROUTE_BLOCKED
# Browser: Disabled-Page + Diagnosepanel (nicht leer)
```

## Evidence-Anker

- `dcc_live_acceptance_after_fallback_api_version_latest.json`
- `dcc_live_acceptance_after_fallback_*_latest.{txt,json}`
- `DCC_BLANK_SCREEN_TRIAGE_RESULT.md` (Vorgänger-Fix `199d3c6`)

## Nächster empfohlener Track

1. Release restore dokumentieren → dann `RUNTIME_GOVERNANCE_LIVE_VALIDATION`
2. Monolith-Boundary erst nach stabiler DCC-/Runtime-Governance
3. Controlled Command Runner **zurückgestellt**
