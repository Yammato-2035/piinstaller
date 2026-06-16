# R.8 — SquashFS R.6 Hook Check

**Datum:** 2026-06-13  
**ISO SHA256:** `18d613e569da4b322f962a1928054d5660280a7ab9626302d2100d3150760390`  
**Methode:** `xorriso -extract /live/filesystem.squashfs` + `unsquashfs -ll/-cat` (read-only)

## Pflichtkomponenten

| Komponente | Status | Pfad im Squashfs |
|------------|--------|------------------|
| `setuphelfer-rescue-boot-evidence-init` | **FOUND** | `usr/local/sbin/` (0755) |
| `setuphelfer-rescue-evidence.py` | **FOUND** | `usr/local/sbin/` |
| `setuphelfer-rescue-start-assistant` | **FOUND** | `usr/local/sbin/` |
| `rescue_persistence.py` | **FOUND** | `opt/setuphelfer-rescue/backend/core/` |
| `rescue_test_matrix.py` | **FOUND** | `opt/setuphelfer-rescue/backend/core/` |
| `initialize_boot_evidence_marker` | **FOUND** | 2 Treffer in persistence.py |
| `boot_marker` / `boot_marker_written` | **FOUND** | persistence.py + test_matrix.py |
| `RESCUE_PERSISTENCE_VERSION = 4` | **FOUND** | persistence.py |
| `evidence.py boot-init` | **FOUND** | Subcommand + `_cmd_boot_init` |
| `start-assistant` boot-hook | **FOUND** | `boot-evidence-init` Aufruf |
| R6 Matrix (`build_r6_boot_persistence_matrix_entries`) | **FOUND** | 2 Treffer |
| MANIFEST `source_head=d62b4a1` | **FOUND** | `opt/setuphelfer-rescue/MANIFEST.json` |
| VERSION im Squashfs | **1.7.18.0** | `opt/setuphelfer-rescue/VERSION` |

## Vergleich pre-R.6 Stick-Squashfs

| Check | pre-R.6 (`f94a1c39…`) | R.8 ISO (`18d613e5…`) |
|-------|----------------------|----------------------|
| `boot-evidence-init` | MISSING | **FOUND** |
| persistence v4 | v3 | **v4** |
| `initialize_boot_evidence_marker` | 0 | **2** |

## Entscheidung

**PASS** — R.6 Boot-Persistence-Hook im Squashfs nachgewiesen.

**Nicht** `blocked_r6_hook_missing`.
