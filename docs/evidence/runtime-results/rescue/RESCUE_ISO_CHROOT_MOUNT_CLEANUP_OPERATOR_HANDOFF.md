# Operator-Handoff — Chroot/Mount-Cleanup (Watchdog-Runtime grün)

**Agent führt nichts mit sudo aus.** Nur dieses Terminal.

```bash
cd /home/volker/piinstaller
BUILD_TREE="/home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live"
./scripts/check-runtime-deploy-gate.sh   # erwarte Exit 0

cd "$BUILD_TREE"
sudo lb clean --purge 2>/dev/null || true
sudo ./auto/clean 2>/dev/null || true

findmnt -R "$BUILD_TREE" -rn -o TARGET | sort -r | while read -r target; do
  case "$target" in
    "$BUILD_TREE"/*)
      echo "unmounting $target"
      sudo umount "$target" 2>/dev/null || sudo umount -l "$target"
      ;;
    "$BUILD_TREE")
      echo "skip build tree root mount: $target"
      ;;
    *)
      echo "REFUSE outside build tree: $target"
      exit 40
      ;;
  esac
done

findmnt -R "$BUILD_TREE" || true
# Nur wenn keine Mounts mehr:
sudo rm -rf binary chroot cache .build local 2>/dev/null || true
findmnt -R "$BUILD_TREE" || true

cd /home/volker/piinstaller
./scripts/rescue-live/prepare-controlled-live-build-tree.sh
grep syslinux-utils "$BUILD_TREE/config/package-lists/setuphelfer.list.binary"

# Optional Build-Retry (nur wenn Cleanup OK):
./scripts/check-runtime-deploy-gate.sh
sudo -v
scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build
echo "wrapper_exit=$?"
```

**Nicht:** USB-Write, Restore, Boot-/VM-Test, Healthcheck-Timer aktivieren.
