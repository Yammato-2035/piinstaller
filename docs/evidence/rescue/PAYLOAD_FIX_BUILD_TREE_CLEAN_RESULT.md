# Payload Fix — Build Tree Clean

**Status:** `blocked`

| Feld | Wert |
|------|------|
| `clean_exit` | **32** — root-owned paths, sudo erforderlich |
| Dry-run | 11 Ziele inkl. `binary.hybrid.iso`, `filesystem.squashfs` |
| stale ISO/squashfs | **nicht entfernt** |

## Operator

```bash
cd /home/volker/piinstaller
sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
```
