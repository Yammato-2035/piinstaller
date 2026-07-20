# Inject-Quellenlücke (Korrektur vor Build)

Beim Offline-Repack aus Commit `30aa68b8` scheiterte
`inject-gui-bvr-fixes-into-stick-squashfs.sh`, weil das Skript feste
`inject`-Pfade auf Workspace-Dateien enthält, die **nicht** in HEAD
committed sind (u. a. ASUS/Pi5/Backup-Plan-Module, untracked).

## Korrektur

- `inject()` überspringt fehlende Quellen mit `[SKIP]`.
- Danach Fail-closed-Prüfung der **Diagnose-Pflichtpfade** im Squash-Root.

Neuer Commit folgt; Build-Worktree wird aus dem neuen HEAD neu erzeugt.
