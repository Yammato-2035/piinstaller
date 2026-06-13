# R.3 Phase 0 — Repo- und Gate-Status

**Kampagne:** R.3 Rettungsstick Boot-/Menü-/Log-/Testmatrix-Stabilisierung  
**Datum:** 2026-06-10  
**HEAD (vor R.3-Arbeit):** `6037a5a`  
**Branch:** `main`  
**Version:** `1.7.15.0` (`config/version.json`)

## Dirty Tree

Working tree **dirty** — viele fremde Änderungen (Rescue-Build, Frontend, Evidence-Artefakte, Submodule `ckb-next`).  
**R.3-Regel:** Nur gezielte R.3-Dateien bearbeitet; keine fremden Dateien angefasst.

## Gates

| Gate | Ergebnis | Details |
|------|----------|---------|
| `check-module-boundaries.sh` | `review_required` | Exit 0 mit Warnungen (app.py groß, duplicate storage, legacy network) |
| `check-runtime-deploy-gate.sh` | **Exit 20** | `LEGACY_GATE_NON_PROFILE_AWARE` — Profil `release`, dev-dashboard 404 erwartet |

**Hinweis:** R.3 ist reine Workspace-Implementierung + Unit-Tests; kein Deploy, kein Runtime-Smoke, kein Hardwaretest.

## Fremdänderungen (nicht von R.3)

- `backend/core/network_info_facade.py`, `route_exposure.py` (vorherige Kampagnen)
- Rescue live-build tree, Payload-Fix-Evidence, DCC-Evidence
- `docs/faq/DEVELOPMENT_CONTROL_CENTER_FAQ_DE.md`, `RESCUE_FAQ.md` (teilweise vorbestehend)

## R.3 Scope-Freigabe

- Kein Restore / Backup-Execute / Partition-Write / Deploy
- Kein `apt install`, kein `systemctl restart` auf Host
- Kein USB-Write ohne explizite Freigabe
- Unit-Tests und `py_compile` nur gegen Workspace

## Nächster Schritt

Phasen 1–10 Implementierung + Tests + Doku (dieser Auftrag).
