# R.8 — Build Tree Prepare + Validate

**Datum:** 2026-06-13  
**Build-Root:** `build/rescue/live-build/setuphelfer-rescue-live`

## Prepare

```bash
./scripts/rescue-live/prepare-controlled-live-build-tree.sh
```

| Feld | Wert |
|------|------|
| Exit | **0** |
| Profil | `standard` |
| React UI Build | success (1.7.18.0) |
| Bundle nach `includes.chroot/opt/setuphelfer-rescue` | 2938 files |

## Validate

```bash
./scripts/rescue-live/validate-controlled-live-build-tree.sh \
  build/rescue/live-build/setuphelfer-rescue-live
```

| Feld | Wert |
|------|------|
| Exit | **11** |
| Grund | `FORBIDDEN: binary.hybrid.iso` (stale pre-R.6 ISO vom 2026-06-13 18:35) |

Validator prüft Tree-Inhalt korrekt bis zum ISO-Artefakt-Check. Stale ISO blockiert Exit 0 — **kein** Tree-Inhaltsfehler.

**Vor Operator-Build:** ISO entfernen oder `auto/clean` / `clean-controlled-live-build-tree.sh` (Operator-Gate).

## MANIFEST im Build-Tree

Pfad: `config/includes.chroot/opt/setuphelfer-rescue/MANIFEST.json`

| Feld | Wert |
|------|------|
| `source_head` | **`d62b4a1`** ✓ |

## R.6-Artefakte im Build-Tree

| Artefakt | Pfad | Status |
|----------|------|--------|
| `setuphelfer-rescue-boot-evidence-init` | `config/includes.chroot/usr/local/sbin/` | **FOUND** (0755) |
| `rescue_persistence.py` v4 | `config/includes.chroot/opt/setuphelfer-rescue/backend/core/` | **FOUND** |
| `rescue_test_matrix.py` R6 | `config/includes.chroot/opt/setuphelfer-rescue/backend/core/` | **FOUND** |
| `setuphelfer-rescue-evidence.py` `boot-init` | `usr/local/sbin/` | **FOUND** |
| `start-assistant` boot-hook | `usr/local/sbin/` | **FOUND** |

## Package-List

| Check | Ergebnis |
|-------|----------|
| `x-www-browser` | **nicht vorhanden** ✓ |
| `chromium` | vorhanden |
| `openbox` | vorhanden |
| `xserver-xorg` | vorhanden |
| `xinit` | vorhanden |

## Bewertung

| Kriterium | Status |
|-----------|--------|
| Tree-Inhalt R.6-ready | **ja** |
| `source_head=d62b4a1` | **ja** |
| validate Exit 0 | **nein** (nur stale ISO) |

**Tree bereit** — validate Exit 11 ist Hygiene-Artefakt, kein R.6-Blocker.
