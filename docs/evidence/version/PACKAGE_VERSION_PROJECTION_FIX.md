# PACKAGE_VERSION_PROJECTION_FIX

**Datum:** 2026-06-05  
**Projektversion:** 1.7.3.1 (unverändert)

## Problem

Backend/API/Frontend melden `1.7.3.1`, Tauri-Build und Bundle heißen weiter `1.7.3` — wirkte wie Versions-Drift, ist aber **Semver-Limitierung**.

## Technische Klärung

| System | Vierstellig (1.7.3.1) | Dreistellig (1.7.3) |
|--------|------------------------|---------------------|
| Cargo `version =` | **Nein** (kein gültiges Semver) | **Ja** |
| Tauri `tauri.conf.json` `version` | **Nein** | **Ja** |
| npm `package.json` | **Ja** | — |
| Debian upstream | **Ja** | — |

## Versionsebenen (nachher)

| Ebene | Wert |
|-------|------|
| setuphelfer_project_version | **1.7.3.1** |
| semver_package_version | **1.7.3** |
| deb_upstream_version | **1.7.3.1** |
| deb_package_revision | **1** |
| cargo_compile_label | **v1.7.3** |

### Mapping-Regel

- **Compile-Zeile** `Compiling pi-installer v1.7.3` = korrekt.
- **Tauri-Default-Bundle:** `SetupHelfer_1.7.3_amd64.deb` = semver-Projektion (Gate: **Warnung** wenn W>0).
- **Soll-Bundle:** `SetupHelfer_1.7.3.1_amd64.deb` via `npm run tauri:build:projected`.

## Umsetzung

- `backend/core/version_projection.py`
- `scripts/check-packaging-version-gate.sh` (Exit 19 bei unbekannter Version)
- `scripts/rename-tauri-bundle-artifacts.sh`
- `frontend/sync-version.js` → `setuphelferProjectVersion`, deb-changelog-Hinweis
- `tauri:build:projected` npm-Script

## Tests

- `test_version_projection_v1.py`
- `test_version_consistency_v1.py` (bestehend)
- `npm run build` — grün

## Commit / Push

- Commit: ja (separater Commit nach Abschluss)
- Push: nein
