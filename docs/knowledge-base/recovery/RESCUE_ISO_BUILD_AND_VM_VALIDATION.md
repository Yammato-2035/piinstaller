# Rescue ISO Build & VM Validation (KB)

Kurzreferenz für **Phase 1**: ISO aus Debian-Live-Tooling bauen, unter `build/rescue/output/` ablegen, in einer **VM** (QEMU) prüfen und die Setuphelfer-Runtime per **HTTP read-only** testen.

## Leitplanken

- Kein `dd` auf USB, kein Restore-Execute, keine Host-Internplatten-Writes aus den Runnern.
- Kontrollierter Operator-Pfad: `scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build`.
- Der eigentliche Live-Build laeuft dabei nur im vorbereiteten Build-Tree mit `./auto/config` und `sudo env PATH="<repo>/build/rescue/tool-compat/bin:$PATH" lb build noauto`.
- Vor dem eigentlichen Build prueft der Wrapper jetzt das Operator-Policy-Gate. Ohne Root, echtes TTY oder dokumentierte `sudo -n`-Allowlist endet der Lauf mit `blocked_requires_operator_sudo_policy` und Exit `30` statt an einer Hintergrund-Passwortabfrage zu haengen.
- **2026-05-27:** Agent/Cursor-Shell ohne TTY → policy block, kein ISO; Operator-Wiederholung im echten Terminal nach `sudo -v` (Evidence: `RESCUE_ISO_MANUAL_OPERATOR_BUILD_CLASSIFICATION.md`).
- **2026-05-28:** `RESCUE-BUILD-CHROOT-CLEANUP-001` — `chroot/proc` + fehlendes `/usr/bin/env` (LB_EXIT=1); zuerst Mount-Cleanup nur unter BUILD_TREE, dann Retry (nicht isohybrid). Handoff: `RESCUE_ISO_CHROOT_MOUNT_CLEANUP_OPERATOR_HANDOFF.md`.
- **2026-05-29:** Hybrid-ISO **`binary.hybrid.iso`** verifiziert (SHA256, `file`, `isoinfo`); `LB_EXIT=1` nur durch stale zsync — Artefakt ≠ Boot-Nachweis. Evidence: `RESCUE_ISO_ARTIFACT_VERIFY.md`. Nächster Schritt: VM-Boot-Prep, kein USB-Write.
- **2026-05-29 (VM prep):** QEMU 8.2.2 vorhanden; Testplan `RESCUE_ISO_VM_BOOT_TEST_PLAN.md`; Smoke **nicht** ausgeführt (kein `VM_BOOT_SMOKE_FREIGEGEBEN`). Nächster Schritt: `RESCUE_ISO_VM_BOOT_SMOKE_OPERATOR_RUN`.
- VM-Sicherheit: `docs/developer/RESCUE_VM_TEST_SAFETY_POLICY.md`.

## Deploy-Doku

- `docs/deploy/DEPLOY_RESCUE_ISO_BUILD_AND_VM_VALIDATION_DE.md` / `_EN.md`
- Evidence-Übersicht: `docs/evidence/DEPLOY_RESCUE_ISO_BUILD_AND_VM_VALIDATION.md`
