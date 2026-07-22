# Capture Finalizer Root Cause — Boot c8c60116 / Run 0ec17061

## Primäre Ursache

Der Capture-Workflow schrieb Identity/BIOS/NVMe-Identität und brach **vor** SMART/Panther/Finalizer ab.
`run_status.json` blieb bei `status=running` und `captures.*.pending`, weil Status und Marker erst am Ende geschrieben wurden und **kein `finally`-Pfad** existierte.

## Sekundäre Ursachen

1. Kein terminaler Zwang (`complete|partial|failed|cancelled`)
2. Keine `COMPLETED.TAG` / `PARTIAL.TAG` / Manifest-vor-Marker-Reihenfolge
3. TUI ohne Phasenfortschritt (nur Infobox „Capture läuft“)

## GUI

`not_applicable_for_text_hardware_discovery` — kein Fehler; Textprofil + `nomodeset` + `skip_gui` sind beabsichtigt.

## Confidence

**high**
