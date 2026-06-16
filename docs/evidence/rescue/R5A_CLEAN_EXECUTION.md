# R.5A Rebuild Unblock — Clean Execution

**Datum:** 2026-06-13

## Geplanter Befehl (Operator-Terminal)

```bash
cd /home/volker/piinstaller
sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
```

## Agent-Versuch

```bash
sudo -n bash scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
```

**Ergebnis:** `sudo: Ein Passwort ist notwendig` — **Exit 1**

**Clean vollständig ausgeführt: nein** (sudo-Clean ausstehend im Operator-TTY)

## Partieller Zwischenstand (ohne sudo)

Einige Top-Level-Artefakte wurden per `mv` nach `build/rescue/.quarantine-r5a-*` verschoben (nicht löschbar als User). **`cache/`** bleibt root-owned und blockiert weiterhin.

```
find build/rescue/live-build/setuphelfer-rescue-live -maxdepth 2 -user root -print | head -5
→ nur cache/ und Unterverzeichnisse
```

## Nach Operator-Clean prüfen

```bash
find build/rescue/live-build/setuphelfer-rescue-live -maxdepth 2 -user root -print | head -50
# Erwartung: leer

PYTHONPATH=backend:. python3 -c "
from core.rescue_iso_build_permission_policy import assess_build_tree_permissions, default_build_tree
print(assess_build_tree_permissions(default_build_tree())['permission_status'])
"
# Erwartung: ready
```

## Erwarteter Clean-Output (Referenz)

```
REMOVED: .../binary
REMOVED: .../cache
...
OK: clean completed
```
