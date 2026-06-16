# R.5A Remediation — Tree Validation

**Build-Root:** `build/rescue/live-build/setuphelfer-rescue-live`  
**Skript:** `./scripts/rescue-live/validate-controlled-live-build-tree.sh`

## Ergebnis

```
OK: apt archive areas complete for firmware packages
OK: build-tree-manifest source_head=57e30d9
STATUS: pre_chroot_ok
SUMMARY: Preflight ok vor chroot-Erzeugung
OK: controlled live build tree validation passed
VALIDATE_EXIT=0
```

## Bewertung

| Status | Wert |
|--------|------|
| Exit-Code | **0** |
| Ergebnis | **`tree_ready_for_rebuild`** |

## Nebenkorrekturen am Validator (Remediation-bedingt)

1. Stale `chroot/`/`binary/` aus Forbidden-Scan ausgenommen (lb-Artefakte ≠ prepared config tree)
2. False-positive SECRET-Scan für Redaction-Regex ausgeschlossen
3. `start-assistant`-Check: `-x` statt fehlerhaftem Inhalt-Grep

## Nebenkorrektur Prepare

`.py`-Skripte in `usr/local/sbin/` erhalten `0755` (Validator verlangt ausführbar).

## Kein ISO-Build

Validator ist read-only; kein `lb build` ausgeführt.
