# Rescue ISO Build & VM Validation (KB)

Kurzreferenz für **Phase 1**: ISO aus Debian-Live-Tooling bauen, unter `build/rescue/output/` ablegen, in einer **VM** (QEMU) prüfen und die Setuphelfer-Runtime per **HTTP read-only** testen.

## Leitplanken

- Kein `dd` auf USB, kein Restore-Execute, keine Host-Internplatten-Writes aus den Runnern.
- Kontrollierter Operator-Pfad: `scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build`.
- Der eigentliche Live-Build laeuft dabei nur im vorbereiteten Build-Tree mit `./auto/config` und `sudo env PATH="<repo>/build/rescue/tool-compat/bin:$PATH" lb build noauto`.
- Vor dem eigentlichen Build prueft der Wrapper jetzt das Operator-Policy-Gate. Ohne Root, echtes TTY oder dokumentierte `sudo -n`-Allowlist endet der Lauf mit `blocked_requires_operator_sudo_policy` und Exit `30` statt an einer Hintergrund-Passwortabfrage zu haengen.
- **2026-06-02 (build-tree cleanup + validate fix):** Operator clean **ok**; Validate Exit 14 war False Positive (`PYTHONPATH` vs. `PATH=`); Fix in `validate-live-build-dpkg-preflight.sh`; Validate danach Exit **0**. Precheck: `ready_for_controlled_iso_build_operator_run`. Evidence: `RESCUE_ISO_VALIDATE_DANGEROUS_PATH_FIX_RESULT.md`.
- **2026-05-28:** `RESCUE-BUILD-CHROOT-CLEANUP-001` — `chroot/proc` + fehlendes `/usr/bin/env` (LB_EXIT=1); zuerst Mount-Cleanup nur unter BUILD_TREE, dann Retry (nicht isohybrid). Handoff: `RESCUE_ISO_CHROOT_MOUNT_CLEANUP_OPERATOR_HANDOFF.md`.
- **2026-05-29:** Hybrid-ISO **`binary.hybrid.iso`** verifiziert (SHA256, `file`, `isoinfo`); `LB_EXIT=1` nur durch stale zsync — Artefakt ≠ Boot-Nachweis. Evidence: `RESCUE_ISO_ARTIFACT_VERIFY.md`. Nächster Schritt: VM-Boot-Prep, kein USB-Write.
- **2026-05-29 (VM prep):** QEMU 8.2.2 vorhanden; Testplan `RESCUE_ISO_VM_BOOT_TEST_PLAN.md`; Smoke **nicht** ausgeführt (kein `VM_BOOT_SMOKE_FREIGEGEBEN`). Nächster Schritt: `RESCUE_ISO_VM_BOOT_SMOKE_OPERATOR_RUN`.
- **2026-05-29 (VM smoke):** Smoke ausgeführt (kein Host-Disk); **timeout_no_boot_signal** nach 120s, 0 Bytes serial stdout; Exit 124. Nächster Schritt: `RESCUE_ISO_VM_BOOT_TIMEOUT_TRIAGE`. Rescue bleibt **yellow**.
- **2026-05-29 (timeout triage):** `-nographic` 600s → **bootloader_seen** (SeaBIOS, iPXE, ISOLINUX); ISO-Inhalt (vmlinuz/initrd/squashfs) auf ISO bestätigt. Nächster Schritt: `RESCUE_ISO_LIVE_SYSTEM_BOOT_VALIDATION`.
- **2026-05-29 (live boot):** nographic **1200s** → `timeout_after_bootloader` (stdout identisch zu 600s); Kernel/Live nicht auf Serial. Nächster Schritt: `RESCUE_ISO_VM_VISUAL_BOOT_OPERATOR_RUN`.
- **2026-05-29 (visual VM):** Operator-QEMU → **Debian 12**, DHCP, runlevel 2, `debian login:` (`live_system_started`). Root-Login fehlgeschlagen; als Nächstes User `live` + Setuphelfer-Check.
- **2026-05-29 (funktional):** Operator: **Kein Setuphelfer**. Offline: Bundle in Squashfs, **Units nicht enabled** (`validate-rescue-iso-squashfs.sh` Exit 12). Rebuild mit aktuellem `prepare-controlled-live-build-tree.sh`; Login **`user`** / **`live`**.
- **2026-05-30 (systemd init fix):** Ursache `bootappend_init_missing`; Fix `init=/lib/systemd/systemd` + dbus; Validator Exit 15 auf alter ISO.
- **2026-05-29 (visual live VM):** user/live, Bundle, DE-Locale OK; **systemd nicht Init** → Backend unreachable. Evidence: `RESCUE_ISO_VISUAL_LIVE_SYSTEM_FUNCTIONAL_VALIDATION_RESULT.md`.
- **2026-05-29 (visual live handoff):** Testplan + Artefakt-Recheck (SHA256, Validator 0); VM-Test wartet auf `VISUAL_LIVE_FUNCTIONAL_FREIGEGEBEN=1`. Evidence: `RESCUE_ISO_VISUAL_LIVE_SYSTEM_FUNCTIONAL_VALIDATION_RESULT.md`.
- **2026-05-29 (integration rebuild ingest):** Operator LB_EXIT=0, Validator Exit **0** — Bundle, systemd enable, DE keyboard/locale, login hints in Squashfs. Rescue **yellow** (VM/USB/Restore offen). Evidence: `RESCUE_ISO_RUNTIME_INTEGRATION_REBUILD_RESULT_INGEST.md`.
- **2026-05-29 (integration rebuild prep):** DE-Tastatur (`de`/`de-latin1`), Locale `de_DE.UTF-8`, Zeitzone `Europe/Berlin`, systemd-wants, MOTD/issue. Rebuild nur mit `RESCUE_RUNTIME_REBUILD_FREIGEGEBEN=1`. Evidence: `RESCUE_ISO_RUNTIME_INTEGRATION_REBUILD_RESULT.md`.
- VM-Sicherheit: `docs/developer/RESCUE_VM_TEST_SAFETY_POLICY.md`.

## Deploy-Doku

- `docs/deploy/DEPLOY_RESCUE_ISO_BUILD_AND_VM_VALIDATION_DE.md` / `_EN.md`
- Evidence-Übersicht: `docs/evidence/DEPLOY_RESCUE_ISO_BUILD_AND_VM_VALIDATION.md`
