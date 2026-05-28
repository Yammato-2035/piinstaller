# Rescue Build Diagnostics

## Zweck

Diese Diagnose-Notiz trennt die aktuellen Rescue-Build-Blocker sauber voneinander, damit das Dashboard und die Evidence keinen generischen "Build fehlgeschlagen"-Eindruck erzeugen.

## RESCUE-BUILD-ROOT-001

- Titel DE: `Rescue-ISO-Build benötigt kontrollierte Root-Ausführung`
- Titel EN: `Rescue ISO build requires controlled root execution`
- Typische Signale:
  - `blocked_requires_operator_sudo_policy`
  - `sudo: ein Terminal ist erforderlich`
  - `sudo: a terminal is required`
  - `sudo: a password is required`
  - `LB_EXIT=1` oder Wrapper-Policy-Exit ohne ISO-Artefakt nach sudo-Block
- Bedeutung:
  - Toolchain, `rsvg` und Live-Build-Tree koennen vorbereitet sein.
  - Der echte Build bleibt trotzdem blockiert, solange kein sicherer Root-Pfad dokumentiert ist.
- Empfehlung:
  - Wrapper aus einem echten Operator-Terminal mit sudo-Rechten starten
  - oder eng begrenzte dokumentierte sudo-Allowlist fuer genau den freigegebenen Wrapper vorbereiten
  - kein Passwort via stdin, kein Askpass-Hack, kein globales `NOPASSWD`

## RESCUE-BUILD-GATE-001

- Titel DE: `Direkter lb build wurde durch kontrolliertes Build-Gate blockiert`
- Titel EN: `Direct lb build was blocked by the controlled build gate`
- Typische Signale:
  - `blocked_controlled_build_gate_required`
  - `Use controlled gate before running lb build.`
  - Exit `20` aus `auto/build`
- Bedeutung:
  - `auto/build` ist absichtlich ein Stop-Script.
  - Zulaessig bleibt nur der kontrollierte Wrapper-/`noauto`-Pfad.

## RESCUE-BUILD-TOOL-001

- Titel DE: `Host-Build-Abhängigkeit für SVG-Konvertierung fehlt oder ist unvollständig`
- Titel EN: `Host build dependency for SVG conversion is missing or incomplete`
- Typische Signale:
  - `blocked_build_tools_missing`
  - `rsvg-convert fehlt`
  - `librsvg2-bin fehlt`
- Bedeutung:
  - Der Build scheitert schon an der Host-Toolchain, bevor der eigentliche ISO-Lauf sinnvoll bewertet werden kann.
  - Setuphelfer installiert die Host-Abhängigkeit nicht automatisch.
- Empfehlung:
  - Dokumentierte Host-Abhängigkeit `librsvg2-bin` installieren
  - danach Preflight erneut lesen, nicht blind weiterbauen

## RESCUE-BUILD-RSVG-001

- Titel DE: `Legacy-rsvg-Erwartung durch live-build erkannt`
- Titel EN: `Legacy rsvg expectation detected from live-build`
- Typische Signale:
  - `blocked_legacy_rsvg_command_missing`
  - `live-build erwartet /usr/bin/rsvg`
  - `rsvg-convert vorhanden, aber rsvg fehlt`
- Bedeutung:
  - Die Host-Abhängigkeit kann bereits vorhanden sein.
  - Das Problem ist dann nicht fehlendes `librsvg2-bin`, sondern eine Legacy-Erwartung an `rsvg`.
- Empfehlung:
  - projektlokalen `rsvg`-Kompatibilitätswrapper verwenden
  - **kein** globaler Symlink nach `/usr/bin/rsvg`

## RESCUE-BUILD-ISOHYBRID-001

- Titel DE: `isohybrid fehlt in der live-build Binary-Stage`
- Titel EN: `isohybrid missing in live-build binary stage`
- Typische Signale:
  - `binary.sh: …: isohybrid: not found`
  - `LB_EXIT=127` nach `extents written` / genisoimage
  - `RESCUE-BUILD-ISOHYBRID-001` im Wrapper-Preflight (Exit **31**)
- Bedeutung:
  - Die Roh-ISO kann bereits unter `chroot/binary.hybrid.iso` liegen; der Hybrid-Schritt ist trotzdem fehlgeschlagen.
  - Live-build installiert für `iso-hybrid` oft nur `syslinux`; `isohybrid` liegt auf Debian in **`syslinux-utils`**.
- Empfehlung:
  - `prepare-controlled-live-build-tree.sh` (legt `setuphelfer.list.binary` an)
  - `./auto/clean` im Build-Verzeichnis
  - Build-Retry im Operator-Terminal
  - optional manuell auf dem Host: `sudo apt install syslinux-utils` (kein Auto-Install durch Setuphelfer)

## RESCUE-BUILD-CHROOT-CLEANUP-001

- Titel DE: `Chroot-/Mount-Cleanup im live-build-Baum fehlgeschlagen`
- Titel EN: `Chroot/mount cleanup failed in live-build tree`
- Typische Signale:
  - `rm: … chroot/proc/… … Vorgang nicht zulässig` / `Operation not permitted`
  - `chroot: failed to run command '/usr/bin/env': No such file or directory`
  - `LB_EXIT=1` nach „Begin unmounting filesystems“
- Bedeutung:
  - **Nicht** isohybrid — der Chroot ist beschädigt oder Pseudo-FS war noch gemountet.
- Empfehlung:
  - `findmnt -R` nur unter BUILD_TREE; umount tiefste zuerst; kein `rm -rf` bei aktiven Mounts
  - `lb clean` / `./auto/clean`, Tree neu vorbereiten, dann Build-Retry (Operator-Terminal)

## RESCUE-BUILD-ARCH-001

- Titel DE: `Zielarchitektur nicht durch aktuellen Build abgedeckt`
- Titel EN: `Target architecture is not covered by the current build track`
- Bedeutung:
  - `amd64` ist der aktuelle aktive Rescue-ISO-Track.
  - `i386` bleibt separater Review-Track.
  - `arm64` und `armhf` bleiben getrennte Image-/Provisioning-Tracks.

## NOTIFICATION-EMAIL-PROVIDER-001

- Titel DE: `E-Mail-Benachrichtigung durch Provider-Limit blockiert`
- Titel EN: `Email notification is blocked by a provider limit`
- Typische Signale:
  - `notification.email.provider_limit_exceeded`
  - `554 5.7.0 outgoing message limit exceeded`
  - `email.status=provider_limit`
- Bedeutung:
  - Dashboard-Event und Klassifikation koennen korrekt sein, waehrend der Mailversand wegen Provider-Limits gelb bleibt.
  - Das ist **kein** Fake-Green fuer den E-Mail-Teil, aber auch kein Grund, den gesamten Dashboard-Status rot zu machen.
- Empfehlung:
  - Provider-Limit / Kontingent / Wartezeit pruefen
  - Dashboard und E-Mail-Teilstatus sauber getrennt halten

## Verknuepfte Dokumentation

- `docs/runbooks/RESCUE_CONTROLLED_ISO_BUILD_RUNBOOK.md`
- `docs/knowledge-base/recovery/RESCUE_ISO_CONTROLLED_BUILD_GATE.md`
- `docs/architecture/RESCUE_TARGET_ARCHITECTURE_MATRIX.md`
- `docs/knowledge-base/dev-dashboard/NOTIFICATIONS.md`
