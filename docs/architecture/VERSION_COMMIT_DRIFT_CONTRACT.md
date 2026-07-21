# Version / Commit / Payload Drift Contract (PI-RS-BVR-GUI-DCC-001)

**Task:** PI-RS-BVR-GUI-DCC-001  
**Implementierung:** `backend/core/version_commit_drift.py`, DCC-Status in `backend/core/rescue_bvr_dcc_status.py`

## Source of Truth (SoT)

| Ebene | Datei / Ort | Feld |
|-------|-------------|------|
| Projektversion | `config/version.json` | `project_version` |
| Rescue-Payload | `config/rescue_payload_version.json` | `rescue_payload_version` |
| Deploy-Manifest | Workspace- und Runtime-Manifeste (Phase-0-Gate) | Commit/Version-Hashes |
| Laufzeit | `/opt/setuphelfer` | `git rev-parse HEAD`, `/api/version` |
| USB-Stick | FAT32-ESP Payload | Version + SHA256 |

Abgeleitete Dateien (`VERSION`, `package.json`, Tauri/Cargo) müssen zur SoT passen — siehe [VERSIONING.md](../developer/VERSIONING.md).

## Identitäten (Drift-Matrix-Zeilen)

| Komponente | Verglichen wird |
|------------|-----------------|
| `workspace` | Workspace-Commit vs. erwarteter Feature-Commit |
| `runtime_opt` | `/opt/setuphelfer`-Commit vs. Workspace/Feature |
| `backend_api` | `GET /api/version` → `project_version` vs. Workspace |
| `frontend` | Frontend-Version vs. Workspace |
| `payload` | `rescue_payload_version` + Build-Commit + SHA256 |
| `usb_stick` | Stick-Payload-Version/SHA256 vs. erwartetes Payload |

Zusätzlich: `origin_main_commit` vs. `workspace_commit` — Feature-Lag auf `main` ist **gelb**, nicht automatisch rot.

## Drift-Typen (`drifts[]`)

| Drift-ID | Bedingung |
|----------|-----------|
| `workspace_runtime_commit_drift` | Runtime-Commit ≠ erwarteter Workspace/Feature-Commit |
| `workspace_runtime_version_drift` | Runtime-Version ≠ Workspace-Version |
| `backend_frontend_version_drift` | API- oder Frontend-Version ≠ Workspace |
| `payload_usb_version_drift` | USB-Payload-Version ≠ erwartete Payload-Version |
| `payload_usb_sha256_drift` | USB-SHA256 ≠ erwarteter Payload-SHA256 |
| `unknown_runtime_identity` | Runtime-Commit/Version nicht ermittelbar |

## Ampel-Regeln

### GREEN

- Alle vergleichbaren Identitätspaare stimmen überein.
- Keine `red`-Drifts; keine fehlenden Pflichtfelder.

### YELLOW

- Dokumentierter, erwarteter Lag (z. B. Feature-Branch vor `origin/main`).
- `classify_identity_pair(..., documented_ok=true)` → absichtliche Abweichung.
- `origin_main_status=yellow` wenn Feature-Commit ≠ `origin/main`.
- DCC: `passed_with_gui_fallback`, `fallback`, `partial`, `incomplete` i18n.

### RED

- Unerwartete Abweichung zwischen Workspace, Runtime, API, Payload oder USB.
- BVR-Kern `failed`.
- GUI `failed` ohne dokumentierten Fallback-Pfad.

### GRAY

- Identität unbekannt (`unknown`, leer, `n/a`).
- Keine Runtime-Evidence (`unknown_runtime_identity`).
- Evidence fehlt (`evidence_status=missing`).

**Regel:** Unbekannt wird **nie** als GREEN interpretiert (`rescue_bvr_dcc_status.py`).

## DCC-Felder (Auszug)

`version_drift_status`, `deploy_drift_status`, `traffic_lights.version_drift`, `traffic_lights.deploy_drift`, `workspace_commit`, `runtime_commit`, `payload_version`, `payload_build_commit`, `usb_payload_sha256`.

## Prüfskripte (Phase 0)

```bash
python3 backend/tools/check_version_consistency.py --repo-root .
./scripts/check-backend-version-gate.sh
./scripts/check-runtime-deploy-gate.sh
```

Exit-Codes: **17** Workspace-Drift, **18** `/opt`/API-Drift, **19** Packaging nicht zuordenbar.

## Schema

Matrix-Schema: `setuphelfer.version-commit-drift-matrix.v1` — siehe `docs/evidence/rescue/bvr-gui-dcc-001/version_drift_matrix.json`.
