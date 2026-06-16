# R.5A Remediation — Package-List Drift

**HEAD:** `57e30d9`  
**Pfad:** `build/rescue/live-build/setuphelfer-rescue-live/config/package-lists/setuphelfer.list.chroot`

## Befund

| Quelle | Zeilen | R.4-Pakete |
|--------|--------|------------|
| Git `57e30d9` | **48** | vorhanden (Z. 38–48) |
| Worktree vor Remediation | **37** | fehlend (endet bei `whiptail`) |

## Fehlende Zeilen (nur in Git HEAD, nicht im Worktree)

```
xserver-xorg
xinit
openbox
chromium
dbus-x11
x11-xserver-utils
unclutter
fonts-dejavu
fonts-noto
x-www-browser
wireless-tools
```

## Root Cause

`scripts/rescue-live/prepare-controlled-live-build-tree.sh` schreibt die Package-Liste per Heredoc und endete bei Zeile 37 (`whiptail`). Der Git-Stand aus R.4 (`57e30d9`) enthält die R.4-Erweiterung, wurde aber vom Prepare-Skript bei jedem Lauf überschrieben.

## `find` — einzige Quelle im Workspace

```
./build/rescue/live-build/setuphelfer-rescue-live/config/package-lists/setuphelfer.list.chroot
```

Kein separates Template außerhalb des Build-Trees; die autoritative Quelle ist Git HEAD + Prepare-Heredoc.

## Drift bestätigt

**ja** — Package-List-Drift war die direkte Ursache für fehlende Browser/Display-Pakete in der gebauten ISO.
