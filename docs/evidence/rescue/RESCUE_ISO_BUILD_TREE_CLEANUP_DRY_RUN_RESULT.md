# Rescue ISO Build-Tree Cleanup — Dry-Run Ergebnis

**Stand:** 2026-06-02  
**Status:** **ok**

## Ausführung

```bash
sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --dry-run
```

| Feld | Wert |
|------|------|
| **dry_run_exit** | **0** |
| **Pfade** | **13** — alle unter `build/rescue/live-build/setuphelfer-rescue-live/` |

## Targets (Auszug)

- `.build`, `binary`, `binary.hybrid.iso`, `binary.contents`, `binary.packages`
- `cache`, `chroot`, `chroot.headers`, `chroot.packages.*`
- `local`, `wget-log*`

## Safety

Keine Treffer für `/dev/`, `dd`, `mkfs`, `wipefs`, `parted`, `restore` außerhalb Build-Tree.

Log: `build/rescue/logs/controlled-iso-build/clean-latest.log` (Operator-Terminal 6)
