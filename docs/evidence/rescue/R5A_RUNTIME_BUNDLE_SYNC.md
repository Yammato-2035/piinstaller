# R.5A Remediation — Runtime-Bundle Sync

**HEAD:** `57e30d9`

## Vorher (Drift)

| Feld | Wert |
|------|------|
| Pfad | `includes.chroot/opt/setuphelfer-rescue/MANIFEST.json` |
| `source_head` | `a8de59e` |
| `files_count` | 2819 |
| R.3 Core-Module | **fehlend** |

**Ursache:** `build/rescue/temp-runtime/setuphelfer-rescue-runtime` war veraltet; `prepare-controlled-live-build-tree.sh` kopiert ausschließlich aus diesem Bundle (`BUNDLE_SRC`).

## Maßnahme

```bash
./scripts/rescue-live/create-temp-runtime-bundle.sh
./scripts/rescue-live/prepare-controlled-live-build-tree.sh
```

## Nachher

| Feld | Wert |
|------|------|
| Temp-Bundle `source_head` | `57e30d9` |
| Staged `source_head` | `57e30d9` |
| `files_count` | **2938** |
| `bundle_manifest_sha256` | `d54f9f826c198dd10bb97c362ebbff9be881cb23dbdfbad4863e783c0254b886` |

## R.3 Modul-Tests (`test -f`)

| Pfad | Ergebnis |
|------|----------|
| `.../backend/core/rescue_persistence.py` | OK |
| `.../backend/core/rescue_test_matrix.py` | OK |
| `.../backend/core/rescue_telemetry_spool.py` | OK |
| `.../backend/core/rescue_evidence_bundle.py` | OK |

## Prepare-Skript-Korrektur

Nicht am Bundle-Kopierpfad geändert — `create-temp-runtime-bundle.sh` war ausreichend. Package-List-Heredoc in `prepare-controlled-live-build-tree.sh` separat korrigiert (siehe `R5A_PACKAGE_LIST_SYNC.md`).

## Status

**Runtime MANIFEST source_head = 57e30d9** — ja
