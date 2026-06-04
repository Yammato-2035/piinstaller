# Rescue ISO Build & VM Validation (KB)

Kurzreferenz für **Phase 1**: ISO aus Debian-Live-Tooling bauen, unter `build/rescue/output/` ablegen, in einer **VM** (QEMU) prüfen und die Setuphelfer-Runtime per **HTTP read-only** testen.

## Leitplanken

- Kein `dd` auf USB, kein Restore-Execute, keine Host-Internplatten-Writes aus den Runnern.
- Kontrollierter Operator-Pfad: `scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build`.
- Der eigentliche Live-Build laeuft dabei nur im vorbereiteten Build-Tree mit `./auto/config` und `sudo env PATH="<repo>/build/rescue/tool-compat/bin:$PATH" lb build noauto`.
- Vor dem eigentlichen Build prueft der Wrapper jetzt das Operator-Policy-Gate. Ohne Root, echtes TTY oder dokumentierte `sudo -n`-Allowlist endet der Lauf mit `blocked_requires_operator_sudo_policy` und Exit `30` statt an einer Hintergrund-Passwortabfrage zu haengen.
- **2026-06-02 (controlled build + ingest):** Operator-Build LB_EXIT=0; Artefakt verified; ready for QEMU guest-agent smoke.
- **2026-06-02 (QEMU guest-agent smoke):** Operator-Autopilot ausgeführt; **blocked** — Serial 0 B, timeout 124, guest_report_missing; Standard-ISO ohne ttyS0 + Autostart-Gap.
- **2026-06-02 (developer-qemu profile fix):** Prepare-only mit `SETUPHELFER_RESCUE_BUILD_PROFILE=developer-qemu`; Serial + Hook 090 materialisiert; Validate blockiert durch stale root-owned `binary/` vom Standard-Build — Operator `sudo ./auto/clean` vor Rebuild. Kein ISO-Build in diesem Lauf.
- **2026-06-02 (rebuild blocker ingest):** Buildversuch LB_EXIT=34, `profile=standard` (Mismatch); 7 root-owned Top-Level-Artefakte; Dry-Run Clean ok; Operator-sudo-Clean ausstehend; Prepare/Validate developer-qemu ok. Kein Build in Ingest-Lauf.
- **2026-06-02 (developer-qemu ISO rebuild verify):** LB_EXIT=0, profile=developer-qemu, ISO SHA `3ee02b36…`, console=ttyS0 in ISO; autopilot unit not in wants — review_required before QEMU smoke. No QEMU in ingest.
- **2026-06-03 (autopilot wants fix):** Static wants symlink in prepare (developer-qemu only); squashfs validator extended; ready for ISO rebuild operator run.
- **2026-06-03 (post-fix rebuild ingest):** Agent blocked exit 30; ISO still pre-fix SHA; operator sudo clean+build required. No QEMU.
- **2026-06-03 (post-fix rebuild success ingest):** Operator LB_EXIT=0, profile=developer-qemu, ISO SHA `614cc86e…`; Autopilot wants in Squashfs; validator exit 0; ready for operator smoke. No QEMU in ingest.
- **2026-06-03 (post-preflight smoke ingest):** No post-ISO-rebuild smoke evidence (`DEVSERVER_PREFLIGHT_OK`, new run_id); ingest **blocked** (`qemu_operator_smoke_incomplete`); release trap ok. Operator re-run required.
- **2026-06-03 (devserver agent ISO report fix):** PYTHONPATH `/opt/setuphelfer-rescue/backend`; `-m devserver_agent.cli`; lab Host header + local_lab TrustedHost `10.0.2.2`; validator import checks; old ISO exit 21; rebuild before QEMU. Evidence: `DEVSERVER_AGENT_ISO_REPORT_FIX_RESULT.md`.
- **2026-06-03 (post port-registry smoke ingest):** Run `qemu_rescue_developer_autopilot_20260603_111427` — Preflight+ISO ok; Serial 135KiB; Autopilot startet; **blocked** — `ModuleNotFoundError: devserver_agent`, Proxy `Invalid Host header`, no host report. No new QEMU in ingest. See `QEMU_GUEST_AGENT_AFTER_REGISTRY_INGEST_RESULT.md`.
- **2026-06-03 (devserver agent fix rebuild+QEMU):** Fix `886a098` im Workspace; **Deploy nach `/opt` blocked** (`sudo` in Agent-Session); ISO-Rebuild und QEMU **nicht** gestartet (STRICT STOP). Evidence: `DEVSERVER_AGENT_FIX_REBUILD_QEMU_RESULT.md`.
- **2026-06-03 (QEMU 212528 ingest):** Operator deploy+ISO rebuild; Run `212528` — ModuleNotFound/Invalid Host **weg**; **`agent_send_failed`**, `guest_report_missing`; Evidence: `QEMU_212528_INGEST_RESULT.md`. USB gesperrt.
- **2026-06-03 (guest report payload fix):** Dev-Server profile/config sync + POST Host header + serial HTTP markers + validator regex; no new QEMU/ISO in triage run. Evidence: `QEMU_GUEST_REPORT_PAYLOAD_TRIAGE_RESULT.md`.
- **2026-06-03 (payload fix rebuild+QEMU verify):** Operator pipeline **blocked** (sudo); partial `/opt` backend sync; prepare ok; validate_tree/clean/build/QEMU nicht ausgeführt. Evidence: `PAYLOAD_FIX_REBUILD_QEMU_RESULT.md`.
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
