# R.5A — Tree Revalidation After Clean

**Datum:** 2026-06-13  
**Hinweis:** Prepare/Validate nach **partiellem** Cleanup (cache noch root-owned). Config-Tree unabhängig von lb-Artefakten.

## Prepare

```bash
./scripts/rescue-live/prepare-controlled-live-build-tree.sh
```

```
OK: controlled live build tree at .../setuphelfer-rescue-live
OK: rescue_build_profile=standard
OK: bundle copied to includes.chroot/opt/setuphelfer-rescue (2938 files ref)
```

## Validate

```bash
./scripts/rescue-live/validate-controlled-live-build-tree.sh \
  build/rescue/live-build/setuphelfer-rescue-live
```

```
OK: apt archive areas complete for firmware packages
OK: build-tree-manifest source_head=57e30d9
STATUS: pre_chroot_ok
SUMMARY: Preflight ok vor chroot-Erzeugung
OK: controlled live build tree validation passed
VALIDATE_EXIT=0
```

## Bewertung

| Check | Ergebnis |
|-------|----------|
| Tree validation Exit | **0** |
| Config-Tree bereit | **ja** |
| Permission preflight | **blocked** (cache root-owned) — Rebuild weiterhin LB_EXIT=34 bis sudo-Clean |
