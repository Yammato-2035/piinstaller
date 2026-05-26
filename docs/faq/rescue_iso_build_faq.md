# Rescue ISO Build FAQ

## Warum blockierte der Preflight trotz installiertem `librsvg2-bin`?

Weil `librsvg2-bin` auf dem Host `rsvg-convert` liefert, das verwendete `live-build`-Skript `lb_binary_syslinux` aber explizit `/usr/bin/rsvg` erwartet und `rsvg --format png ...` aufruft.

## Reicht `rsvg-convert` allein?

Nicht für den aktuellen `syslinux`-Theme-Pfad von `live-build`. Es reicht aber aus, um einen kontrollierten projektlokalen Kompatibilitätswrapper zu speisen.

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

## Was ist jetzt die kurzfristig sichere Loesung?

Den Wrapper aus einem echten Operator-Terminal mit gueltigen `sudo`-Rechten starten. Alternativ kann der Operator eine eng begrenzte sudo-Allowlist fuer genau diesen dokumentierten Wrapper vorbereiten. Setuphelfer installiert dabei **keine** Policy automatisch.

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
