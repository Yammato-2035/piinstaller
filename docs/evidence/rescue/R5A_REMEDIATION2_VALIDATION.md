# R.5A Remediation-2 — Validation

**Datum:** 2026-06-13

## Befehl

```bash
./scripts/rescue-live/validate-controlled-live-build-tree.sh \
  build/rescue/live-build/setuphelfer-rescue-live
```

## Ergebnis

```
OK: apt archive areas complete for firmware packages
OK: build-tree-manifest source_head=57e30d9
STATUS: ok
SUMMARY: DPKG preflight ok; chroot enthält dpkg und start-stop-daemon
OK: controlled live build tree validation passed
VALIDATE_EXIT=0
```

## x-www-browser Guard

Validator würde bei `x-www-browser` in list.chroot mit Exit **15** abbrechen (`RESCUE-ISO-INVALID-PACKAGE-001`). Aktuell: **kein Treffer**.

## Bewertung

**Validator Exit 0** — Remediation-2 package-list fix verifiziert.
