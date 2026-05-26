# Rescue ISO Build & VM Validation (KB)

Kurzreferenz für **Phase 1**: ISO aus Debian-Live-Tooling bauen, unter `build/rescue/output/` ablegen, in einer **VM** (QEMU) prüfen und die Setuphelfer-Runtime per **HTTP read-only** testen.

## Leitplanken

- Kein `dd` auf USB, kein Restore-Execute, keine Host-Internplatten-Writes aus den Runnern.
- Kontrollierter Operator-Pfad: `scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build`.
- Der eigentliche Live-Build laeuft dabei nur im vorbereiteten Build-Tree mit `./auto/config` und `sudo env PATH="<repo>/build/rescue/tool-compat/bin:$PATH" lb build noauto`.
- VM-Sicherheit: `docs/developer/RESCUE_VM_TEST_SAFETY_POLICY.md`.

## Deploy-Doku

- `docs/deploy/DEPLOY_RESCUE_ISO_BUILD_AND_VM_VALIDATION_DE.md` / `_EN.md`
- Evidence-Übersicht: `docs/evidence/DEPLOY_RESCUE_ISO_BUILD_AND_VM_VALIDATION.md`
