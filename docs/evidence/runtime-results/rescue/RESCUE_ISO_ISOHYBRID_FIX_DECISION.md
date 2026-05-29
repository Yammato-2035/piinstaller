# Rescue ISO isohybrid — Fix Decision (korrigiert)

**Entscheidung:** **`syslinux-utils` in `setuphelfer.list.chroot`** (Chroot-Paketliste)

## Begründung

- `lb_binary_iso` führt `genisoimage` und `isohybrid` im **live-build-Chroot** aus (`Chroot chroot "sh binary.sh"`).
- `Check_package chroot/usr/bin/isohybrid syslinux` installiert nur **`syslinux`** — auf Bookworm liegt `isohybrid` in **`syslinux-utils`**.
- `config/package-lists/*.list.binary` wird von **`lb_binary_package-lists`** nur in den **ISO-APT-Pool** (`binary/pool/…`) geschrieben, **nicht** in den Chroot installiert.
- Daher schlägt der Build trotz `setuphelfer.list.binary` und sichtbarem `syslinux-utils` in `binary.contents` fehl.

## Frühere Annahme (widerrufen)

| Annahme | Status |
|---------|--------|
| Nur `setuphelfer.list.binary` reicht | **falsch** — Pool ≠ Chroot |

## Operator

1. `./scripts/rescue-live/prepare-controlled-live-build-tree.sh`
2. Prüfen: `grep -x syslinux-utils config/package-lists/setuphelfer.list.chroot`
3. **Vollständiges** Stage-Cleanup (`chroot`, `cache`, `binary`, `.build`, …), dann Build-Retry
4. Nach Chroot-Phase optional: `test -x chroot/usr/bin/isohybrid` im BUILD_TREE

JSON: `rescue_iso_isohybrid_fix_decision_latest.json`
