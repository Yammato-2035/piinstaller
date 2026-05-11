# Rescue Orchestrator Execute – KB

## Warum Preview-Session Pflicht ist

Execute ohne gültige Preview wäre ein Blindflug. Session + Token binden Backup/Ziel eindeutig an die vorher geprüfte Vorschau.

## Warum vor Execute erneut Safety und Verify?

Zwischen Preview und Execute kann sich der Systemzustand ändern. Re-Check verhindert, dass ein ehemals zulässiges Ziel später unsicher wird.

## Warum kein automatisches Boot-Repair?

Phase 2 fokussiert kontrollierten Dateirestore. Boot-Reparatur bleibt explizit getrennt und wird nicht automatisch nach Execute ausgelöst.
