# Controlled Command Runner Design (DE)

## Zweck

- interne Entwicklerläufe im Dev Dashboard
- vollständiges Logging (stdout/stderr getrennt)
- Exit-Code-Auswertung und Safety-Klassifikation
- Evidence-Erzeugung pro Run
- Unterstützung für Roadmap-Delta-Vorschläge
- kein Endnutzerfeature

## Nicht-Ziele

- kein freies Terminal
- keine freie Shell
- kein `sudo` aus Dashboard
- kein Restore/Backup/USB/apt
- keine Operator-Eskalation aus UI

## Safety-Klassen

- `read_only`
- `test_only`
- `evidence_only`
- `operator_handoff`
- `forbidden`

## Beispiele

### `read_only` erlaubt

- `git status --short`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `git log -1 --oneline`
- `./scripts/check-runtime-deploy-gate.sh`
- `curl /api/version`
- `curl /api/dev-dashboard/status`
- `python3 -m json.tool <allowlisted-json>`
- `findmnt -R <allowlisted-build-tree>`
- `command -v <tool>`

### `test_only` erlaubt

- `bash -n scripts/rescue-live/*.sh`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test -- --run`
- `backend/venv/bin/python3 -m unittest <allowlisted_module>`

### `operator_handoff` (nicht direkt ausführbar)

- `sudo -v`
- `sudo systemctl start setuphelfer-deploy-helper.service`
- controlled rescue build
- controlled chroot cleanup
- `sudo umount` unter Build-Tree
- `sudo rm -rf` nur nach Mount-Cleanup und nur unter Build-Tree

### `forbidden`

- freie Shell
- freies sudo
- `apt install`/`upgrade`
- `dd`
- `mkfs`
- `parted write`
- restore start
- backup start
- USB write
- `chmod`/`chown` auf Systempfaden
- sudoers ändern
- `curl` auf beliebige externe URLs
