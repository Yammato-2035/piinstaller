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

## Warum ist `amd64` nicht automatisch „supported“, obwohl es der Hauptkandidat ist?

Weil ohne echten Build- und Boot-Nachweis kein Ziel final grün markiert wird. `amd64` ist deshalb aktuell nur `primary_candidate`.

## Warum ist `i386` nicht wegen Chrome-`i386`-Warnungen blockiert?

Weil Browser-/Chrome-Repos für den Rescue-MVP nicht automatisch relevant sind. `i386` bleibt ein eigenes Review-Ziel, aber nicht pauschal wegen solcher Fremdwarnungen blockiert.

## Warum werden `arm64` und `armhf` getrennt behandelt?

Weil ARM andere Bootloader-, Firmware- und Image-Anforderungen hat als der x86-ISO-Track. Diese Ziele bleiben deshalb separate Deferred-Tracks.

## Warum bleibt USB-Write trotz verbessertem Preflight blockiert?

Weil USB-Write, `dd`, `mkfs` und Partition-Writes weiterhin ein separates Safety-Gate benötigen und nicht Teil dieser Triage sind.
