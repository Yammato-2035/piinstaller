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

## Warum `isohybrid: not found` nach „extents written“ (LB_EXIT=127)?

`lb_binary_iso` erzeugt zuerst die ISO per `genisoimage`, führt danach **`binary.sh` im Binary-Chroot** aus und ruft dort `isohybrid` auf. Live-build installiert für `iso-hybrid` oft nur das Paket **`syslinux`** — auf Debian/Ubuntu liegt **`isohybrid`** in **`syslinux-utils`**.

- Diagnose: **`RESCUE-BUILD-ISOHYBRID-001`**
- Fix im Repo: `prepare-controlled-live-build-tree.sh` legt `config/package-lists/setuphelfer.list.binary` mit `syslinux-utils` an
- Operator: Tree vorbereiten, `./auto/clean`, Build-Retry — **kein** automatisches `apt install` durch Setuphelfer
- Optional auf dem Build-Host (bewusst, manuell): `sudo apt install syslinux-utils` (hilft nur für Host-Debugging; der Lauf scheitert im **Chroot**)

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
