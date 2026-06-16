# R.8 — Tree Revalidation After Clean

**Datum:** 2026-06-13

## Status

| Feld | Wert |
|------|------|
| Clean ausgeführt | **nein** (sudo blockiert) |
| Prepare erneut | **nicht ausgeführt** (Clean-Voraussetzung fehlt) |

## Validate (aktueller Stand, ohne Clean)

```bash
./scripts/rescue-live/validate-controlled-live-build-tree.sh \
  build/rescue/live-build/setuphelfer-rescue-live
```

| Feld | Wert |
|------|------|
| Exit | **11** |
| Grund | `FORBIDDEN: binary.hybrid.iso` (stale, root-owned) |

## Erwartung nach erfolgreichem Operator-Clean + Prepare

| Schritt | Erwartung |
|---------|-----------|
| Clean | root-owned → 0 |
| Prepare | Exit 0, `source_head=d62b4a1` |
| Validate | **Exit 0** |

## Entscheidung

**BLOCKED** — Revalidation nach Clean ausstehend.
