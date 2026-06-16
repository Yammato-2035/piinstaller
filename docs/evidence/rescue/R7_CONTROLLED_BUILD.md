# R.7 — Controlled ISO Build

**Datum:** 2026-06-10

## Anfrage

```bash
./scripts/rescue-live/run-controlled-iso-build-with-logging.sh \
  --operator-confirm-build --profile standard
```

## Ergebnis

| Feld | Wert |
|------|------|
| `build_started` | **false** |
| `LB_EXIT` | **30** |
| `error_code` | `blocked_requires_operator_sudo_policy` |
| `POLICY_IS_TTY` | false |
| `POLICY_SUDO_NONINTERACTIVE` | false |
| `run_id` | `rescue_developer_iso_20260613_180416` |

## Bestehendes ISO (unverändert)

| Feld | Wert |
|------|------|
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| Größe | 1 348 468 736 Bytes (~1,3 GiB) |
| SHA256 | `f94a1c399e345ae297262fb76e01bae0e350b941334a183cd39080dfa4cb9143` |
| Build-Zeitpunkt | 2026-06-13 18:35 (vor R.6-Workspace-Fix) |

## Entscheidung

**blocked_operator_build** — Neues ISO mit R.6-Hook erfordert Operator-Terminal mit `sudo`.

Summary: `docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json`
