# R.8 — R.6 Build Tree Quick Check

**Datum:** 2026-06-13  
**Build-Root:** `build/rescue/live-build/setuphelfer-rescue-live`  
**Hinweis:** Prüfung am vorbereiteten Tree (nach letztem `prepare`, vor erfolgreichem Clean).

## Ergebnis

| Check | Erwartung | Status |
|-------|-----------|--------|
| MANIFEST `source_head` | `d62b4a1` | **OK** |
| `setuphelfer-rescue-boot-evidence-init` | vorhanden | **OK** (`usr/local/sbin/`, 0755) |
| `initialize_boot_evidence_marker` | in persistence.py | **OK** |
| `RESCUE_PERSISTENCE_VERSION` | 4 | **OK** |
| R6-Matrix (`build_r6_boot_persistence_matrix_entries`) | vorhanden | **OK** (2 Treffer) |
| `x-www-browser` | fehlt | **OK** |
| `chromium` | vorhanden | **OK** |
| `openbox` | vorhanden | **OK** |
| `xserver-xorg` | vorhanden | **OK** |
| `xinit` | vorhanden | **OK** |

## Bewertung

**R.6 Build-Tree-Inhalt: PASS**

Blocker ist **nicht** R.6-Staging, sondern root-owned Live-Build-Artefakte + stale ISO.
