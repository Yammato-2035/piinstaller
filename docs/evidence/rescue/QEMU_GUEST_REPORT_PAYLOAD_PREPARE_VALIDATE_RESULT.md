# QEMU Guest Report Payload — Prepare / Validate Result

| Phase | Exit | Status |
|-------|------|--------|
| prepare | **0** | ok — `developer-qemu`, Autopilot+Marker materialisiert |
| validate_tree | **11** | **review_required** — stale `binary/live/filesystem.squashfs` (FORBIDDEN) vom Prior-Build |

## Bewertung

Fixes im **config/**-Tree nach Prepare verifiziert (SEND-Marker, `devserver_agent.cli`).

**Operator sudo clean** erforderlich vor validate_tree=0 und ISO-Rebuild:

```bash
sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
```

## ISO-Validator (bestehendes ISO, neuer Regex)

`validate_iso_exit=0` auf altem Artefakt — Regex-Gap behoben.

**Gesamt:** `review_required` (validate_tree blockiert durch stale binary/, nicht durch Fix-Inhalt)
