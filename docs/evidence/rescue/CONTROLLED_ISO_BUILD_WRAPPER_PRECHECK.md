# Controlled ISO Build — Wrapper Precheck

**Stand:** 2026-06-02  
**Status:** **ok**

## Kontrollierte Skripte

| Skript | Rolle |
|--------|--------|
| `run-controlled-iso-build-with-logging.sh` | Build-Entry mit **`--operator-confirm-build`** Gate |
| `prepare-controlled-live-build-tree.sh` | Tree-Vorbereitung, rsvg-Compat, kein `lb build` |
| `validate-controlled-live-build-tree.sh` | Read-only Tree-Validierung |
| `validate-rescue-iso-squashfs.sh` | Post-Build Squashfs-Check |
| `clean-controlled-live-build-tree.sh` | Cleanup mit **`--operator-confirm-clean`** |
| `preflight-developer-controlled-iso-build.sh` | Read-only Preflight JSON |

## Pflichtbewertung

| Kriterium | Status |
|-----------|--------|
| Controlled wrapper vorhanden | **yes** |
| Build ohne `--operator-confirm-build` blockiert | **yes** |
| Log/Summary-Pfade | `build/rescue/logs/controlled-iso-build/` |
| USB-Write im Build-Wrapper | **no** |
| Restore im Build-Wrapper | **no** |
| Agent apt install | **no** |

Syntax: `bash -n scripts/rescue-live/*.sh` — **ok** (kein Fehler).
