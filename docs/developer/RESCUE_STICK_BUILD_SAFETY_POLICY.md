# Rescue Stick Build — Safety Policy

Diese Richtlinie gilt für **Planungs- und Build-Vorbereitungsphasen** sowie spätere kontrollierte ISO-Erstellung im Setuphelfer-Repository.

## Erlaubt

- ISO-Erzeugung **nur** innerhalb des Projektbaums, Zielbasis: `build/rescue/`.
- Dokumentation, Runner, API-Handoffs und Tests, die **keine** privilegierten Host-Operationen ausführen.
- Cursor/Agent: Buildbefehle **vorbereiten** (Skripte, README), aber **nicht** automatisch `live-build`, `dd`, oder Paketinstallation auf dem Host des Entwicklers ausführen.

## Verboten (ohne separates Gate)

- Schreibzugriffe auf rohe Blockgeräte `/dev/sdX`, `/dev/nvme*`, Host-Systempartitionen.
- `dd`, `mkfs`, `mount`/`umount` auf **echten** Zielsystemen des Anwenders aus Runnern oder CI ohne explizites Gate.
- `systemctl`-Änderungen am Host durch Deploy-Runner.
- USB-Schreiben mit Image-Flash außerhalb eines **explizit** definierten USB-Write-Gates (später).
- Root-weite Paketinstallationen durch Python-Runner (`apt install` o. Ä.).

## Pfade

- Alle Build-Artefakte: `build/rescue/` (Staging, Cache, Logs, ISO-Ausgabe).
- Evidence-Handoffs: `docs/evidence/runtime-results/handoff/` wie bei bestehenden Deploy-Runnern.

## Skript `scripts/rescue/build-rescue-iso.sh`

- Standardlauf: **Dry-Run** ohne `live-build`-Ausführung.
- Erweiterung nur mit expliziter Umgebungsvariable (siehe Skriptkopf); fehlendes `lb` führt zu klarer Fehlermeldung **ohne** automatische Installation.
