# FAQ: Development Server (DE)

## Sendet der öffentliche Rettungsstick automatisch Daten?

**Nein.** Public Rescue sendet nie automatisch. Auto-Upload ist standardmäßig blockiert.

## Was ist Beta Opt-in?

Freiwilliger, redigierter Auszug. Sensitive Felder werden gehasht oder entfernt.

## Was ist Local Lab?

Eigene Testhardware. Developer Edition darf an den lokalen Dev-Server senden (mit Token).

## Ist SSH sicher?

Nur read-only Allowlist-Profile. Default: SSH deaktiviert. Kein sudo, kein dd/mkfs/mount.

## Kann ich Backup/Restore remote starten?

**Nein** — nicht in diesem MVP. Später nur backup-gated.

## Wo liegen die Daten?

`docs/evidence/runtime-results/dev-server/`

## Wie aktiviere ich den Server?

Siehe `docs/runbooks/DEV_SERVER_LOCAL_LAB_SETUP_DE.md` und `.env.example.devserver`.
