# R.8 — Temp-Runtime Bundle Validation

**Datum:** 2026-06-13  
**Skript:** `./scripts/rescue-live/create-temp-runtime-bundle.sh`  
**Exit:** **0**

## Bundle-Pfad

`build/rescue/temp-runtime/setuphelfer-rescue-runtime/`

## MANIFEST.json

| Feld | Wert |
|------|------|
| `source_head` | **`d62b4a1`** ✓ |
| `files_count` | 2938 |

Hinweis: `project_version` nicht als Top-Level-Feld im MANIFEST; `VERSION`-Datei im Bundle enthält 1.7.18.0.

## Pflichtdateien

| Pfad | Status |
|------|--------|
| `.../backend/core/rescue_persistence.py` | **FOUND** |
| `.../backend/core/rescue_test_matrix.py` | **FOUND** |
| `.../scripts/rescue-live/image/setuphelfer-rescue-boot-evidence-init` | **MISSING** |

### Erklärung boot-evidence-init fehlt im temp-runtime

`create-temp-runtime-bundle.sh` kopiert nur:

- `backend/`
- `frontend/dist/`
- wenige Localonly-Skripte (`start-backend-localonly.sh`, …)

Rescue-Image-Skripte (`scripts/rescue-live/image/*`) werden **nicht** ins temp-runtime-Bundle aufgenommen. Das ist **by design** — der Hook landet über `prepare-controlled-live-build-tree.sh` direkt in `includes.chroot/usr/local/sbin/`.

## Backend-Inhalt (R.6)

| Check | Ergebnis |
|-------|----------|
| `RESCUE_PERSISTENCE_VERSION = 4` | **ja** |
| `initialize_boot_evidence_marker` | **2 Treffer** |

## `find` Ergebnis

```
build/rescue/temp-runtime/setuphelfer-rescue-runtime/backend/core/rescue_persistence.py
build/rescue/temp-runtime/setuphelfer-rescue-runtime/backend/core/rescue_test_matrix.py
```

## Bewertung

**PASS** für Backend-Bundle (`source_head=d62b4a1`, persistence v4).  
Shell-Hook **nicht** im temp-runtime erwartet — Validierung erfolgt im Build-Tree (Phase 2B).
