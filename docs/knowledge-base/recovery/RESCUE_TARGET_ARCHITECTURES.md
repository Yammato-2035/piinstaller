# Rescue Target Architectures

## Warum die Ziele getrennt werden

Der Rescue-ISO-Pfad muss Host-Architektur und Zielarchitektur sauber unterscheiden. Ein `amd64`-Host und ein `amd64`-Rescue-ISO sind nicht automatisch gleichbedeutend mit Unterstützung für `i386`, `arm64` oder `armhf`.

## Aktuelle Einordnung

- `amd64`
  Primärer Kandidat für den x86-Rescue-ISO-Pfad.
  Erwarteter Bootpfad: `BIOS/UEFI`.
  Zielformat: `ISO`.
  Noch nicht final grün, solange Build- und Boot-Evidence fehlen.

- `i386`
  Separates x86-Ziel mit eingeschränkter moderner UEFI-/Treiberlage.
  Erwarteter Bootpfad: `BIOS/limited UEFI`.
  Zielformat: `ISO`.
  Status: `review_required`.

- `arm64`
  Separater ARM-Track mit eigener Firmware-/Kernel-/Image-Strategie.
  Erwarteter Bootpfad: `board_specific / UEFI teilweise`.
  Zielformat: `image`.
  Status: `deferred`.

- `armhf`
  Nur für ausgewählte ältere Geräte sinnvoll.
  Erwarteter Bootpfad: `board_specific`.
  Zielformat: `image`.
  Status: `deferred`.

## Wichtige Abgrenzungen

- ARM läuft nicht „einfach mit“ im normalen x86-ISO-Track.
- `i386` wird nicht durch eine Chrome-`i386`-Repo-Warnung blockiert; Browser-Pakete sind für den Rescue-MVP nicht automatisch relevant.
- `USB-Write` bleibt auch bei positivem Preflight separat blockiert.
