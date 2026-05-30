# FAQ: Development Rescue Agent (DE)

## Sendet der Public Rescue Stick automatisch?

**Nein.** Default-Modus `public_rescue` blockiert Auto-Upload.

## Wann sendet der Agent?

Nur wenn `SETUPHELFER_DEV_AGENT_ENABLED=true` und Modus `local_lab` mit `AUTO_UPLOAD=true`.

## Ist der Agent read-only?

**Ja.** Nur Allowlist-Kommandos, kein sudo, kein mount/dd/mkfs.

## Was passiert wenn der Server down ist?

Berichte werden in `docs/evidence/runtime-results/dev-agent-spool/` gespoolt.

## SSH?

**Nein** — Agent nutzt kein SSH.
