# Rescue Temp Runtime Bundle — Result

**Datum:** 2026-05-24  
**Git HEAD:** `d3d8029`  
**Bundle-Pfad (lokal, nicht versioniert):** `build/rescue/temp-runtime/setuphelfer-rescue-runtime/`

## Erzeugung

```bash
./scripts/rescue-live/create-temp-runtime-bundle.sh
./scripts/rescue-live/validate-temp-runtime-bundle.sh build/rescue/temp-runtime/setuphelfer-rescue-runtime
```

| Feld | Wert |
|------|------|
| **Validator Exit** | **0** (ok) |
| **MANIFEST files_count** | 2777 |
| **MANIFEST sha256** | `ab27953250d1bb76d0d4b1700334faae95545c8f6f631fd0196ff1140b3aaa59` |
| **source_head** | `d3d8029` |
| **rescue_temp_runtime** | true |
| **no_real_build_execution** | true |
| **CDN in frontend/dist** | keine Google-Fonts |
| **ISO/IMG in Bundle** | keine (cache/*.img ausgeschlossen) |
| **backend/venv** | vorhanden |

## Ausgeschlossen vom Bundle

- `backend/tests/`, `backend/cache/`, `.venv`, `.venv-ci`
- `__pycache__`, `.env`, `node_modules`, `*.img`, `*.iso`

## Nächster Schritt

Operator: `docs/runbooks/RESCUE_TEMP_RUNTIME_COPY_TO_LIVE_MEDIUM.md`
