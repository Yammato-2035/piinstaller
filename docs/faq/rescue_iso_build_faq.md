# Rescue ISO Build FAQ

## Warum blockierte der Preflight trotz installiertem `librsvg2-bin`?

Weil `librsvg2-bin` auf dem Host `rsvg-convert` liefert, das verwendete `live-build`-Skript `lb_binary_syslinux` aber explizit `/usr/bin/rsvg` erwartet und `rsvg --format png ...` aufruft.

Diagnostisch sind das deshalb zwei verschiedene Fälle:

- `RESCUE-BUILD-TOOL-001`: Host-Abhängigkeit fehlt (`rsvg-convert` / `librsvg2-bin`)
- `RESCUE-BUILD-RSVG-001`: Legacy-`rsvg` wird zusätzlich erwartet, obwohl `rsvg-convert` schon da ist

## Reicht `rsvg-convert` allein?

Nicht für den aktuellen `syslinux`-Theme-Pfad von `live-build`. Es reicht aber aus, um einen kontrollierten projektlokalen Kompatibilitätswrapper zu speisen.

**Wichtig:** Der Host-`PATH`-Wrapper unter `build/rescue/tool-compat/bin/rsvg` reicht **nicht** — `lb build` ruft `rsvg` **im Chroot** auf. Der Wrapper muss unter `config/includes.chroot/usr/local/bin/rsvg` liegen (setzt `prepare-controlled-live-build-tree.sh`). Fehlerbild: `/usr/bin/env: 'rsvg': No such file or directory`, `LB_EXIT=127`.

## Warum `cannot open binary/isolinux/bootlogo` (LB_EXIT=2)?

`lb_binary_syslinux` erwartet eine `bootlogo`-cpio-Datei im isolinux-Zielverzeichnis. Das Debian-`live-build`-Theme liefert nur `splash.svg.in` — kein fertiges `bootlogo`. `prepare-controlled-live-build-tree.sh` legt deshalb ein minimales Seed-`bootlogo` unter `config/bootloaders/isolinux/bootlogo` an.

**Zusätzlich:** Wenn `binary/isolinux/` von einem abgebrochenen Lauf noch existiert, landet `isolinux.tmp` als Unterordner (`binary/isolinux/isolinux.tmp/`) — dann wird `splash.svg.in` nicht verarbeitet. Vor erneutem Build:

```bash
cd build/rescue/live-build/setuphelfer-rescue-live
./auto/clean
```

Bei root-eigenen Resten ggf. `sudo rm -rf binary chroot cache .build local` im Build-Verzeichnis.

## Warum `rm: chroot/proc ... Vorgang nicht zulässig` und danach `/usr/bin/env` fehlt (LB_EXIT=1)?

Das ist **`RESCUE-BUILD-CHROOT-CLEANUP-001`**, nicht isohybrid:

- live-build versuchte `chroot/proc` zu löschen, während proc noch gemountet war oder der Chroot bereits halb zerstört ist.
- Danach fehlt `/usr/bin/env` im Chroot — der Baum ist unvollständig.

**Vorgehen:**

1. `findmnt -R build/rescue/live-build/setuphelfer-rescue-live` — nur Mounts **unter** dem Build-Tree.
2. Tiefste Mounts zuerst `umount` (ggf. `umount -l`), **kein** `rm -rf` solange Mounts aktiv sind.
3. `lb clean` / `./auto/clean`, dann `sudo rm -rf binary chroot cache .build local` nur ohne Mounts.
4. `prepare-controlled-live-build-tree.sh`, dann kontrollierter Build-Retry im Operator-Terminal.

## Warum `isohybrid: not found` nach „extents written“ (LB_EXIT=127)?

`lb_binary_iso` erzeugt zuerst die ISO per `genisoimage`, führt danach **`binary.sh` im Binary-Chroot** aus und ruft dort `isohybrid` auf. Live-build installiert für `iso-hybrid` oft nur das Paket **`syslinux`** — auf Debian/Ubuntu liegt **`isohybrid`** in **`syslinux-utils`**.

- Diagnose: **`RESCUE-BUILD-ISOHYBRID-001`**
- Fix im Repo: `syslinux-utils` in **`setuphelfer.list.chroot`** (entscheidend); `list.binary` allein reicht nicht (nur ISO-APT-Pool)
- Operator: Tree vorbereiten, vollständiges Cleanup (chroot+cache), Build-Retry — **kein** automatisches `apt install` durch Setuphelfer

## Ist `binary.hybrid.iso` ein gültiges ISO-Artefakt?

Ja. live-build erzeugt für `iso-hybrid` die Datei **`binary.hybrid.iso`** (ohne `.iso`-Suffix). Der kontrollierte Wrapper erkennt diesen Namen explizit.

Artefaktprüfung (sha256, `file`, optional `isoinfo`) ist **nicht** gleich Boot-Nachweis — Rescue bleibt ohne VM/USB/Boot **yellow**, nicht full-green.

## Warum `LB_EXIT=1` mit `binary.hybrid.iso.zsync.xz: Die Datei existiert bereits`?

**`RESCUE-BUILD-ZSYNC-STALE-001`:** Die Hybrid-ISO kann bereits existieren; der Build scheitert danach an veralteten zsync-Resten.

- Rescue-Konfiguration: **`--zsync false`** in `auto/config`
- Cleanup: `auto/clean` entfernt `binary*.zsync*`
- ISO trotzdem mit `sha256sum`/`file` prüfen — nicht als „ISO fehlt“ werten

## Ist VM-Boot-Smoke dasselbe wie Artefaktprüfung oder USB-Test?

**Nein.** Drei getrennte Stufen:

1. **Artefakt** — sha256, `file`, `isoinfo` (read-only auf der ISO-Datei)
2. **VM-Smoke** — QEMU headless mit `-cdrom`, **ohne** `-hda`/Host-Disk; erfordert `VM_BOOT_SMOKE_FREIGEGEBEN`
3. **USB/Hardware** — separates Gate, weiterhin blockiert

Plan: `docs/evidence/runtime-results/rescue/RESCUE_ISO_VM_BOOT_TEST_PLAN.md`  
Policy: `docs/developer/RESCUE_VM_TEST_SAFETY_POLICY.md`

**Ergebnis 2026-05-29:** Ein 120s-QEMU-Lauf ohne `-hda` endete mit Exit **124** und **0 Bytes** stdout → `timeout_no_boot_signal` (kein Fake-Boot-Green). Ohne KVM/TCG kann längerer Timeout nötig sein. Evidence: `RESCUE_ISO_VM_BOOT_SMOKE_RESULT.md`.

**Timeout-Triage 2026-05-29:** Mit **`-nographic`** und **600s** erscheinen SeaBIOS, iPXE und **ISOLINUX** — das beweist Bootfähigkeit im VM, nicht ISO-Defekt. `-display none -serial stdio` war für dieses Image ungeeignet. Evidence: `RESCUE_ISO_VM_BOOT_TIMEOUT_TRIAGE_RESULT.md`.

**Live-System 2026-05-29:** **1200s nographic** ergab dieselben 374 Bytes (nur ISOLINUX) — **kein** Kernel/Live auf Serial. Bootloader ≠ Live-System. Nächster Schritt: visueller Operator-Smoke. Evidence: `RESCUE_ISO_LIVE_SYSTEM_BOOT_VALIDATION_RESULT.md`.

**Visueller VM-Boot 2026-05-29:** Grafisches QEMU zeigt **Debian 12** bis **`debian login:`** — Live-System in VM belegt. `root` an der Konsole schlägt fehl; typisch ist User **`live`**. Evidence: `RESCUE_ISO_VM_VISUAL_BOOT_OPERATOR_RESULT.md`.

**Kein Setuphelfer (Operator 2026-05-29):** Bundle liegt in der Squashfs unter `/opt/setuphelfer-rescue`, startet aber nicht (Units nicht in `multi-user.target.wants`). Login: **`user`** / Passwort **`live`**. Nach Rebuild mit aktuellem `prepare-controlled-live-build-tree.sh` erneut testen. Evidence: `RESCUE_ISO_LIVE_SYSTEM_FUNCTIONAL_VALIDATION_RESULT.md`.

## Login, Tastatur und Locale im Rescue-Live

| Thema | Wert |
|-------|------|
| Login | **`user`** / Passwort **`live`** |
| root | an der Konsole **gesperrt** — nicht als Standard-Login |
| Hostname (Ziel) | `setuphelfer-rescue` (bootappend) |
| Konsole | `KEYMAP=de-latin1` (`/etc/vconsole.conf`) |
| X11 | `XKBLAYOUT="de"` (`/etc/default/keyboard`) |
| Locale | `LANG=de_DE.UTF-8` |
| Zeitzone | `Europe/Berlin` |
| Bundle-Pfad | `/opt/setuphelfer-rescue` |

**Squashfs-Validator** (`validate-rescue-iso-squashfs.sh`): Exit **0** nur wenn Bundle, enabled Units, DE-Layout und Login-Hinweis in der ISO sind. Exit **12** = systemd enable fehlt (alte ISO vor Rebuild).

**Host vs. VM:** `/opt/setuphelfer-rescue` und Rescue-`systemctl` nur **in der gebooteten ISO-VM** prüfen — nicht auf dem Host unter `/opt/setuphelfer`.

## Rebuild Runtime-Integration erfolgreich (2026-05-29)

Operator-Rebuild mit `RESCUE_RUNTIME_REBUILD_FREIGEGEBEN=1`: **LB_EXIT=0**, `validate-rescue-iso-squashfs.sh` **Exit 0**.

| ISO | SHA256 (Kurz) | Validator |
|-----|---------------|-----------|
| neu (16:01) | `3731d123…` | **0** |
| alt (13:49) | `03d5aa95…` | 12 |

Evidence: `RESCUE_ISO_RUNTIME_INTEGRATION_REBUILD_RESULT_INGEST.md`. VM-Funktionstest steht noch aus.

## VM-Funktionstest (visuell)

Freigabe: `VISUAL_LIVE_FUNCTIONAL_FREIGEGEBEN=1`. Plan: `RESCUE_ISO_VISUAL_LIVE_SYSTEM_FUNCTIONAL_TEST_PLAN.md`. Prüfungen **nur in der gebooteten VM** — nicht auf dem Host.

**Operator 2026-05-29:** Login user/live, `/opt/setuphelfer-rescue` vorhanden, DE-Keyboard/Locale/Zeitzone OK. **systemd nicht PID 1** → `systemctl` und `curl :8000` fehlgeschlagen.

**Ursache (2026-05-30):** Bootappend ohne `init=/lib/systemd/systemd`. Fix im Build-Tree; Validator Exit **15** auf alter ISO. Evidence: `RESCUE_ISO_SYSTEMD_INIT_STATIC_ANALYSIS.md`.

## Warum legt Setuphelfer keinen globalen Symlink nach `/usr/bin/rsvg` an?

Weil das eine globale Systemänderung wäre. Setuphelfer soll den Host nicht stillschweigend verändern. Deshalb wird ein projektlokaler Wrapper bevorzugt.

## Wo liegt der Wrapper?

Unter `build/rescue/tool-compat/bin/rsvg`.

Er wird nur verwendet, wenn der spätere Operator-Build den `PATH` explizit um dieses Verzeichnis erweitert.

## Warum startet Setuphelfer den echten ISO-Build nicht direkt?

Weil der echte Build weiterhin ein separater Operator-Schritt mit eigenem Gate bleibt. Auch ein positiver Preflight hebt die Schreib- und Build-Sicherheitsgrenzen nicht auf.

## Warum wurde ein direkter `lb build` mit Exit 20 gestoppt?

Weil `auto/build` im kontrollierten Live-Build-Tree absichtlich nur das Safety-Gate darstellt. Der zulaessige Build-Pfad ist nicht `lb build`, sondern der kontrollierte Operator-Aufruf mit `./auto/config` und `lb build noauto` beziehungsweise `scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build`.

## Warum wurde der Wrapper-Lauf mit `blocked_requires_operator_sudo_policy` gestoppt?

Weil der Wrapper in einer Umgebung ohne echtes Terminal und ohne dokumentierte `sudo -n`-Policy lief. Das ist **kein** `rsvg`-, Toolchain- oder `live-build`-Konfigurationsfehler, sondern ein eigener Root-/Operator-Policy-Blocker.

**Stand 2026-05-27 (Manual Operator Prompt):** Cursor/Agent-Shell ohne TTY → Exit **30**, `build_started=false`, kein ISO. Evidence: `docs/evidence/runtime-results/rescue/RESCUE_ISO_MANUAL_OPERATOR_BUILD_CLASSIFICATION.md`. Wiederholung nur im **echten Operator-Terminal** nach `sudo -v` (kein `sudo -S`, kein Askpass).

## Was ist jetzt die kurzfristig sichere Loesung?

Den Wrapper aus einem echten Operator-Terminal mit gueltigen `sudo`-Rechten starten. Alternativ kann der Operator eine eng begrenzte sudo-Allowlist fuer genau diesen dokumentierten Wrapper vorbereiten. Setuphelfer installiert dabei **keine** Policy automatisch.

## Warum ist nach dem Diagnostics-Testtrack jetzt ein Operator-Terminal-Prompt der naechste Schritt?

Weil die wiederholten Rescue-Build-Fehler jetzt diagnostisch klassifiziert und dokumentiert sind. Der naechste technische Blocker ist damit nicht mehr "Was ist eigentlich kaputt?", sondern der echte kontrollierte Operator-Build in einem Terminal mit sauberem Root-/Policy-Rahmen.

## Was ist ausdruecklich nicht erlaubt?

- Passwortweitergabe ueber stdin
- Askpass-Hacks
- pauschales/globales `NOPASSWD`
- direkter `lb build`
- globale `rsvg`-Symlinks oder Aenderungen an `/usr/lib/live/build`

## Warum ist `amd64` nicht automatisch „supported“, obwohl es der Hauptkandidat ist?

Weil ohne echten Build- und Boot-Nachweis kein Ziel final grün markiert wird. `amd64` ist deshalb aktuell nur `primary_candidate`.

## Warum ist `i386` nicht wegen Chrome-`i386`-Warnungen blockiert?

Weil Browser-/Chrome-Repos für den Rescue-MVP nicht automatisch relevant sind. `i386` bleibt ein eigenes Review-Ziel, aber nicht pauschal wegen solcher Fremdwarnungen blockiert.

## Warum werden `arm64` und `armhf` getrennt behandelt?

Weil ARM andere Bootloader-, Firmware- und Image-Anforderungen hat als der x86-ISO-Track. Diese Ziele bleiben deshalb separate Deferred-Tracks.

## Warum bleibt USB-Write trotz verbessertem Preflight blockiert?

Weil USB-Write, `dd`, `mkfs` und Partition-Writes weiterhin ein separates Safety-Gate benötigen und nicht Teil dieser Triage sind.
