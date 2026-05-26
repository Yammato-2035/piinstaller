# Rescue Operator Policy

## Ziel

Der kontrollierte Rescue-ISO-Build darf Root-Rechte nicht implizit, nicht im Hintergrund und nicht ueber unsichere Passwortweitergabe erhalten.

## Kurzfristige Policy

- bevorzugt: echtes Operator-Terminal mit interaktivem `sudo`
- alternativ: eng begrenzte sudo-Allowlist nur fuer den dokumentierten Wrapper
- nicht erlaubt:
  - Passwort ueber stdin
  - Askpass-Hacks
  - pauschales/globales `NOPASSWD`
  - direkter `lb build`

## Produktpfad spaeter

- separater Root-Helper oder `systemd-run`-/Polkit-basierter Pfad
- eigener Test- und Freigabe-Track
- nicht Teil des aktuellen Rescue-ISO-Policy-Fixes

## Dashboard-Folgerung

Das Rescue-Dashboard zeigt `operator_policy_gate` separat von Toolchain, `rsvg`, Build-Tree und USB-Write:

- `review_required`, wenn der Pfad fachlich klar ist, aber noch ein dokumentierter Root-Kontext fehlt
- `ready`, wenn ein sicherer Root-Pfad bereitsteht
- `blocked`, wenn schon die allgemeinen Build-Voraussetzungen noch nicht erfuellt sind
