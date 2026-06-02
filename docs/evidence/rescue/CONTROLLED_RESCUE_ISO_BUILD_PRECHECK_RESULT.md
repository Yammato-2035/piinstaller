# Controlled Rescue ISO Build — Precheck Ergebnis (NO BUILD)

**Stand:** 2026-06-02 (nach dangerous_path_override-Fix)  
**HEAD:** `11453c5` (Commit folgt)  
**Status:** **`ready_for_controlled_iso_build_operator_run`**

## Cleanup (Operator)

| Phase | Ergebnis |
|-------|----------|
| Dry-Run | **ok** (13 Build-Tree-Pfade) |
| Operator-Clean | **ok** — inkl. Prior `binary.hybrid.iso` |
| Prepare | **ok** |
| Validate (vor Fix) | **Exit 14** — `dangerous_path_override` |
| Validate (nach Fix) | **Exit 0** |

## dangerous_path_override

| Feld | Wert |
|------|------|
| Blocker | `PYTHONPATH=/opt/setuphelfer-rescue` in `setuphelfer-dev-agent.service:10` |
| Ursache | False Positive: `PATH=` matchte Substring in `PYTHONPATH=` |
| Lösung | Eng begrenzte Allowlist + Regex-Fix in `validate-live-build-dpkg-preflight.sh` |
| Globale `/opt`-Freigabe | **nein** |

## Freigabe

**`ready_for_controlled_iso_build_operator_run`** — Validate Exit 0, kein Build in diesem Lauf.

Rescue bleibt **nicht grün** ohne neues ISO + Bootnachweis.

## Nächster Schritt

**CONTROLLED RESCUE ISO BUILD OPERATOR RUN** mit `--operator-confirm-build`.

JSON: `controlled_iso_build_precheck_latest.json`  
Evidence: `RESCUE_ISO_VALIDATE_DANGEROUS_PATH_FIX_RESULT.md`
