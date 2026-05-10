# Rescue Sandbox — Controlled Copy (KB)

## Zweck

Nach der reinen **Planung** (`sandbox_*_copy_plan.json`) erlaubt diese Phase erstmals **echte Dateikopien** — aber nur innerhalb von `build/rescue/sandbox/`, mit festem Maximalgroesse pro Datei, Text-/Nicht-Binaer-Heuristiken fuer Config, Verbot fuer ISO/IMG/QCOW2 und typische Build-Artefakte, atomischem Schreiben und anschliessender **SHA256-Verifikation**.

## Warum Hashes

Jede kopierte Datei wird mit Quell- und Zielhash im Ergebnis-JSON festgehalten; Verify vergleicht On-Disk-Bytes erneut. So erkennen Manipulationen, Teilwrites oder falscher Plan ohne Build-Schritt.

## Kein Build

Diese Kette ersetzt **keinen** Debian-Live- oder ISO-Build: es werden nur geplante Text-/Konfigurationspfade in die Sandbox gespiegelt und geprueft.

## Verweise

- Deploy (DE): `docs/deploy/DEPLOY_RESCUE_SANDBOX_CONTROLLED_COPY_DE.md`
- Deploy (EN): `docs/deploy/DEPLOY_RESCUE_SANDBOX_CONTROLLED_COPY_EN.md`
- Evidence: `docs/evidence/DEPLOY_RESCUE_SANDBOX_CONTROLLED_COPY.md`
- Runner: `backend/deploy/runner_rescue_sandbox_controlled_copy.py`
