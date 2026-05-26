# Rescue Target Architecture Matrix

## Ziel

Die Rescue-Build-Planung trennt strikt zwischen Host-Architektur, Build-Ziel, Bootloader-Familie und Image-Format. Ein erfolgreiches `amd64`-Preflight bedeutet **nicht**, dass `i386`, `arm64` oder `armhf` automatisch mitabgedeckt sind.

## Grundsatz

- `amd64` bleibt der primaere x86-Rescue-Kandidat.
- `i386` ist ein separates Review-Ziel und wird **nicht** aus `amd64` abgeleitet.
- `arm64` und `armhf` bleiben getrennte Image-/Provisioning-Tracks.
- Kein Ziel ist final freigegeben, solange kein Build- und Boot-Nachweis vorliegt.

## Matrix

- `amd64`
  Primärkandidat für x86_64 / AMD64 / Intel 64.
  Erwarteter Bootpfad: `BIOS/UEFI`.
  Zielformat: `ISO`.
  Bootloader-Familie: `syslinux/grub`.
  Status: `primary_candidate`.

- `i386`
  Separates 32-bit-x86-Ziel.
  Erwarteter Bootpfad: `BIOS/limited UEFI`.
  Zielformat: `ISO`.
  Bootloader-Familie: `syslinux/grub (legacy focus)`.
  Status: `review_required`.
  Hinweis: nicht wegen Chrome-/Browser-Repos blockieren; diese Warnungen sind für den Rescue-MVP nicht automatisch relevant.

- `arm64`
  Separater 64-bit-ARM-Track.
  Erwarteter Bootpfad: `board_specific / UEFI teilweise`.
  Zielformat: `image`.
  Bootloader-Familie: `board_firmware_or_uefi`.
  Status: `deferred`.

- `armhf`
  Separater 32-bit-ARM-Track für ausgewählte Altgeräte.
  Erwarteter Bootpfad: `board_specific`.
  Zielformat: `image`.
  Bootloader-Familie: `board_firmware`.
  Status: `deferred`.

## Konsequenzen

- ARM wird nicht als normales x86-ISO-Ziel behandelt.
- `i386` bleibt ein bewusstes eigenes Build-Ziel mit eigener Review- und Testspur.
- `USB-Write` bleibt weiterhin separat blockiert.
- Ein grüner Runtime-/Preflight-Status bedeutet maximal: bereit für einen **separaten** Build-Preflight oder Operator-Build-Schritt.
