# Runbook — Controlled Rescue ISO Build

**Version:** 1.4
**real_iso_build_allowed:** `false` (bis explizite Operator-Freigabe)
**usb_write_allowed:** `false`

## Zweck

Schritt-für-Schritt-Anleitung für einen **kontrollierten** Debian-Live-ISO-Build mit integriertem Setuphelfer Temp-Runtime-Bundle — **ohne** automatische Ausführung.

## Voraussetzungen

0. **Precheck (2026-06-02):** Cleanup **ok**; Validate Exit **0**; Operator-Build **LB_EXIT=0** — Artefakt ingestiert, `ready_for_qemu_guest_agent_smoke`. Evidence: `CONTROLLED_RESCUE_ISO_BUILD_RESULT.md`.
1. **Phase 0:** `./scripts/check-runtime-deploy-gate.sh` → Exit **0**
2. **Toolcheck:** `docs/evidence/rescue/RESCUE_CONTROLLED_LIVE_BUILD_TOOL_CHECK.md` — `lb`, `xorriso`, `mksquashfs`, `grub-mkrescue` vorhanden
3. **RSVG-Preflight:** Dashboard-/Executor-Status darf **nicht** `blocked_build_tools_missing` fuer `rsvg` melden
4. **Temp-Bundle:** Validator Exit **0**
5. **Build-Tree:** `validate-controlled-live-build-tree.sh` Exit **0** (inkl. `syslinux-utils` in **`setuphelfer.list.chroot`**, `--zsync false`)
6. **Binary-Stage / isohybrid:** Preflight prüft `setuphelfer.list.chroot`; Exit **31** bei fehlendem `syslinux-utils` (`RESCUE-BUILD-ISOHYBRID-001`).
7. **Artefakt:** Erfolgreicher Hybrid-Build liefert **`binary.hybrid.iso`** (nicht nur `*.iso`). Artefaktprüfung ≠ Boot-Nachweis.
8. **zsync:** Bei `RESCUE-BUILD-ZSYNC-STALE-001` ISO nicht verwerfen — stale `binary*.zsync*` entfernen oder `--zsync false` nutzen.
7. **Operator-Freigabe** schriftlich (Issue/Ticket/E-Mail)
7. **Operator-Policy-Gate:** Safe Root-Ausführung ist dokumentiert:
   - kurzfristig bevorzugt: echtes Operator-Terminal mit `sudo`
   - alternativ: eng begrenzte sudo-Allowlist für genau den dokumentierten Wrapper
   - Produkt-Roadmap: separater `systemd`-/Root-Helper
   - **nicht erlaubt:** Passwort über stdin, Askpass-Hacks, globales `NOPASSWD`, direkter `lb build`

## Vorbereitung (Repo)

```bash
./scripts/rescue-live/create-temp-runtime-bundle.sh
./scripts/rescue-live/validate-temp-runtime-bundle.sh \
  build/rescue/temp-runtime/setuphelfer-rescue-runtime

# Standard-Release-ISO (defensiv: quiet splash, kein QEMU-Autopilot):
./scripts/rescue-live/prepare-controlled-live-build-tree.sh

# Developer-QEMU-ISO (Serial ttyS0 + Autopilot-Hook 090 — für QEMU Guest-Agent Smoke):
SETUPHELFER_RESCUE_BUILD_PROFILE=developer-qemu \
  ./scripts/rescue-live/prepare-controlled-live-build-tree.sh

./scripts/rescue-live/validate-controlled-live-build-tree.sh \
  build/rescue/live-build/setuphelfer-rescue-live
```

**Profil-Hinweis (2026-06-02):** QEMU-Autopilot-Smoke erfordert **developer-qemu**-Profil. Standard-ISO (`quiet splash`, kein `console=ttyS0`, Autopilot nicht enabled) führt zu Serial 0 B / `guest_report_missing`. Evidence: `DEVELOPER_QEMU_PROFILE_FIX_RESULT.md`.

**Rebuild-Blocker (2026-06-02):** Versuch `rescue_developer_iso_20260602_212524` — **LB_EXIT=34**, `profile=standard` (Mismatch). Vor Build: `sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean`. Build nur mit `--profile developer-qemu` (Log-Zeile `profile=developer-qemu` prüfen; bei `profile=standard` STOP). Evidence: `DEVELOPER_QEMU_REBUILD_OPERATOR_HANDOFF.md`.

## Build-Verzeichnis

```
build/rescue/live-build/setuphelfer-rescue-live/
```

## Chroot-/Mount-Cleanup (RESCUE-BUILD-CHROOT-CLEANUP-001)

**2026-06-02:** Operator-QEMU-Autopilot `qemu_rescue_developer_autopilot_20260602_202725` — **blocked** (Serial 0 B, Exit 124, `guest_report_missing`). Root cause: Standard-ISO ohne `console=ttyS0` + Autopilot nicht enabled. Evidence: `QEMU_GUEST_AGENT_FAILURE_CLASSIFICATION.md`.

Wenn der letzte Lauf mit `chroot/proc` + „Vorgang nicht zulässig“ und fehlendem `/usr/bin/env` endet:

1. **Nur** Mountpoints unter `BUILD_TREE` mit `findmnt -R` prüfen.
2. Tiefste zuerst `umount` — **kein** `rm -rf` auf `chroot` bei aktiven Mounts.
3. `sudo lb clean --purge`, `./auto/clean`, dann ggf. `sudo rm -rf binary chroot cache .build local`.
4. `prepare-controlled-live-build-tree.sh` erneut.
5. Erst dann Build-Retry.

Vollständige Befehle: `docs/evidence/runtime-results/rescue/RESCUE_ISO_CHROOT_MOUNT_CLEANUP_OPERATOR_HANDOFF.md`.

## Nach dem Build (Squashfs-Integration)

```bash
./scripts/rescue-live/validate-rescue-iso-squashfs.sh \
  build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso
```

| Exit | Bedeutung |
|------|-----------|
| **0** | Bundle, enabled Units, DE-Tastatur/Locale/Zeitzone, Login-Hinweis user/live, Konto `user` in `/etc/passwd` |
| **11** | Setuphelfer-Bundle/Runtime-Marker fehlt in Squashfs |
| **12** | systemd-Units nicht in `multi-user.target.wants` |
| **13** | Keyboard/Locale/Timezone (de / de_DE.UTF-8 / Europe/Berlin) fehlt |
| **14** | Login-/MOTD-Hinweis user/live fehlt |
| **15** | `init=/lib/systemd/systemd` fehlt in ISOLINUX `live.cfg` (PID 1 nicht systemd) |
| **16** | `/usr/sbin/init` kein systemd-Symlink (nur wenn init= bootappend fehlt) |
| **17** | dbus fehlt in Squashfs |
| **18** | Konto `user` fehlt in Squashfs-`/etc/passwd` (live-config SysV läuft nicht mit `init=/lib/systemd/systemd`) |

**Rebuild-Freigabe:** `RESCUE_RUNTIME_REBUILD_FREIGEGEBEN=1`, `RESCUE_SYSTEMD_REBUILD_FREIGEGEBEN=1` oder `RESCUE_CHROOT_REBUILD_FREIGEGEBEN=1`.

**Wichtig nach Hook-/Config-Änderungen:** live-build überspringt sonst den Chroot (`skipping binary_rootfs, already done`, Build ~15 s statt ~15–30 min). Mit Rebuild-Freigabe führt der Wrapper `./auto/clean` automatisch aus, wenn Config neuer als `binary/live/filesystem.squashfs` ist. Manuell:

```bash
cd build/rescue/live-build/setuphelfer-rescue-live
sudo ./auto/clean
```

Danach erneut `run-controlled-iso-build-with-logging.sh --operator-confirm-build`. Post-build läuft `validate-rescue-iso-squashfs.sh` — **LB_EXIT=0 allein reicht nicht**, wenn Validator Exit **18** meldet.

**Login im Live-System:** `user` / `live` — **root** an der Konsole ist gesperrt.

**Nach erfolgreichem Rebuild (2026-05-29):** `validate-rescue-iso-squashfs.sh` Exit **0** bestätigt Bundle, enabled Units, DE-Layout und Login-Hinweise in der Squashfs. VM-Funktionstest ist separater Schritt mit `VISUAL_LIVE_FUNCTIONAL_FREIGEGEBEN=1` — siehe `RESCUE_ISO_VISUAL_LIVE_SYSTEM_FUNCTIONAL_TEST_PLAN.md`.

## Operator-Terminal (Pflicht für echten Build)

```bash
cd /home/volker/piinstaller
sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
sudo -v   # interaktiv, gleiche Shell — kein Passwort über stdin
scripts/rescue-live/run-controlled-iso-build-with-logging.sh \
  --operator-confirm-build \
  --profile developer-qemu
# Erste Log-Zeile MUSS profile=developer-qemu enthalten — sonst abbrechen
echo "wrapper_exit=$?"
```

**Nicht** aus Cursor-Agent-Shells ohne TTY: Policy-Guard blockiert mit Exit **30** (`blocked_requires_operator_sudo_policy`). Evidence 2026-05-27: `RESCUE_ISO_MANUAL_OPERATOR_BUILD_CLASSIFICATION.md`.

## Dashboard-Primärweg

1. `GET /api/dev-dashboard/rescue-iso/status` oder Cockpit-Panel **Rettungsstick ISO-Build**
2. Falls stale root-owned State erkannt wird:
   - `POST /api/dev-dashboard/rescue-iso/operator-commands/sudo-clean`
3. Bundle/Tree-Schritte über:
   - `POST /api/dev-dashboard/rescue-iso/step`
4. Build nur als:
   - `POST /api/dev-dashboard/rescue-iso/operator-commands/build`
   - oder spaeter ueber `build_iso_with_sudo`, falls ein sicheres Backend-sudo-Konzept explizit aktiviert ist

Wenn `next_operator_action.type = build_dependency_required`, bleibt der Build blockiert. In diesem Fall zeigt das Dashboard nur den Operator-Hinweis fuer die fehlende Build-Abhaengigkeit, derzeit:

```bash
sudo apt install librsvg2-bin
```

Dieser Hinweis wird **nur angezeigt**, nicht automatisch ausgefuehrt.

Bei **`RESCUE-BUILD-ISOHYBRID-001`** (`isohybrid: not found`, oft nach `extents written`):

1. `./scripts/rescue-live/prepare-controlled-live-build-tree.sh`
2. `cd build/rescue/live-build/setuphelfer-rescue-live && ./auto/clean`
3. Build-Retry (Operator-Terminal, siehe oben)
4. Optional Host (nur manuell): `sudo apt install syslinux-utils` — Setuphelfer installiert nicht automatisch

Evidence: `docs/evidence/runtime-results/rescue/RESCUE_ISO_ISOHYBRID_FAILURE.md`

## Bevorzugter Operator-Pfad (nach Operator-Freigabe)

```bash
scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build
```

Der Wrapper setzt den projektlokalen `rsvg`-Wrapper im `PATH` voran, fuehrt `./auto/config` aus und startet danach den echten Build als:

```bash
cd build/rescue/live-build/setuphelfer-rescue-live
export PATH="/home/volker/piinstaller/build/rescue/tool-compat/bin:$PATH"
./auto/config
sudo env PATH="/home/volker/piinstaller/build/rescue/tool-compat/bin:$PATH" lb build noauto
```

Vor `./auto/config` und `lb build` prueft der Wrapper jetzt explizit:

- ob bereits Root-Rechte aktiv sind
- ob der Aufruf in einem echten TTY/Operator-Terminal laeuft
- ob `sudo -n true` als enge Non-Interactive-Policy funktioniert

Wenn **keine** sichere Root-Ausführung verfuegbar ist, wird **kein** Build gestartet. Der Wrapper beendet dann mit Exit `30` und meldet:

```text
blocked_requires_operator_sudo_policy
Run this command from an operator terminal with sudo privileges or install the documented allowlisted policy.
```

**NICHT automatisch ausführen**, solange das Dashboard `operator_required` meldet.

Wenn das Dashboard `build_dependency_required` oder `blocked_build_tools_missing` meldet, **kein** `lb build` starten. Zuerst die benoetigte Build-Abhaengigkeit am Build-Host bereitstellen und den Preflight erneut pruefen.

`auto/build` im Repo ist absichtlich blockiert (Exit 20). Ein direkter Aufruf wie `lb build` ohne `noauto` ist deshalb verboten und wird bewusst vom Gate gestoppt.

## Operator-Policy-Gate

Das Developer Dashboard zeigt den Root-Bedarf jetzt als eigenes Gate:

- `status=review_required`, wenn der Buildpfad vorbereitet ist, aber noch ein echtes Operator-Terminal oder eine dokumentierte Allowlist-Policy fehlt
- `error_code=blocked_requires_operator_sudo_policy`, wenn ein Wrapper-Lauf genau daran scheiterte
- `status=ready` erst dann, wenn ein dokumentierter Root-Pfad fuer den kontrollierten Build zur Verfuegung steht

Das Rescue-ISO bleibt trotz dieses Fortschritts **gelb**, bis ein echtes ISO-Artefakt vorliegt. USB-Write, Boot-Test und Restore bleiben getrennte Folgephasen.

## Erwartete Artefakte (nach Build)

- `live-image-amd64.hybrid.iso` (Pfad kann je nach live-build-Version variieren)
- SHA256 dokumentieren:

```bash
sha256sum live-image-amd64.hybrid.iso
```

## Nach Build

1. Evidence aktualisieren (`RESCUE_CONTROLLED_ISO_BUILD_RESULT.md` + Summary JSON)
2. **Kein USB-Write** in dieser Phase
3. USB-Schreiben: separater Auftrag → `RESCUE_USB_WRITE_GATE_RUNBOOK.md`

## Development Dashboard / Logs

- Status: `GET /api/dev-dashboard/rescue-iso/status` oder Cockpit-Panel **Rettungsstick ISO-Build**
- Step-Logs:
  - `build/rescue/logs/controlled-iso-build/latest.log`
  - `build/rescue/logs/controlled-iso-build/actions/<action_id>.log`
  - `build/rescue/logs/controlled-iso-build/actions/<action_id>.json`
- Summary:
  - `docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json`
- Operator muss Terminalausgaben nicht mehr manuell sammeln — Dashboard ist der Primärweg

## Aktuelle Fehlerhinweise

- stale root-owned live-build state
- `chroot_package-lists.install` stale
- `skipping ... already done`
- `tar failed` / `File exists` in `debootstrap.log`

## Clean-Hinweis

- `auto/clean` darf **kein** rekursives `lb clean` ausführen
- bevorzugter kontrollierter Clean im Build-Tree:

```bash
cd /home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live
sudo rm -rf .build chroot cache binary local
```

## Verboten ohne Gate

- `dd`, `mkfs`, `parted write`
- Restore, Backup, Verify Deep
- Allowlist-Erweiterung
- Safety-Gate abschwächen

## VM-Boot-Smoke (nach Artefaktprüfung)

- Artefaktprüfung (sha256/file/isoinfo) ist **nicht** Boot-Nachweis.
- Testplan: `docs/evidence/runtime-results/rescue/RESCUE_ISO_VM_BOOT_TEST_PLAN.md`
- Policy: `docs/developer/RESCUE_VM_TEST_SAFETY_POLICY.md`
- Nur mit **`VM_BOOT_SMOKE_FREIGEGEBEN`** im Operator-Lauf; QEMU ohne `-hda`, ohne Host-Disk, ohne USB.
- Evidence: `RESCUE_ISO_VM_BOOT_SMOKE_RESULT.md`
- **Hinweis:** Timeout ohne Serial-Output ist **kein** Boot-Erfolg; TCG ohne KVM kann >120s brauchen.
- **nographic:** Für verifiziertes `binary.hybrid.iso` liefert `-nographic` (nicht `-display none`) BIOS/ISOLINUX-Signale; siehe `RESCUE_ISO_VM_BOOT_TIMEOUT_TRIAGE_RESULT.md`.
- **Live-System:** 1200s nographic reichte nicht für Kernel/Live auf Serial (`timeout_after_bootloader`); visueller Operator-Smoke als Nächstes — `RESCUE_ISO_LIVE_SYSTEM_BOOT_VALIDATION_RESULT.md`.

## Referenzen

- `RESCUE_USB_WRITE_GATE_RUNBOOK.md`
- `RESCUE_STICK_CONTROLLED_ISO_PREPARATION_GATE.md`
- `README_SETUPHELFER_RESCUE_LIVE.md` (im Build-Tree)
