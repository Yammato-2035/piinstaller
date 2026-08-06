# Treiber- und Firmwareauflösung — Rescue Stick

Stand: PI-RS-HW-COMPAT-PROVISION-001 (Phase 19), erweitert um
PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 14).

Sprachen: [Deutsch](DRIVER_FIRMWARE_RESOLUTION_DE.md) · [English](DRIVER_FIRMWARE_RESOLUTION_EN.md) · [Français](DRIVER_FIRMWARE_RESOLUTION_FR.md) · [Nederlands](DRIVER_FIRMWARE_RESOLUTION_NL.md)

Verwandt: [`docs/architecture/DRIVER_FIRMWARE_RESOLUTION_ARCHITECTURE.md`](../architecture/DRIVER_FIRMWARE_RESOLUTION_ARCHITECTURE.md).

## Zweck

Aus Rohdaten der Hardware-Inventur entsteht ein **Vorschlag** für
Treiber-/Firmwareaktivierung — ohne diesen auszuführen.

## Resolver-Stufen (`backend/core/driver_resolver.py`)

1. Kernel-Modalias auswerten
2. gebundenen Treiber prüfen (`kernel_driver_in_use`)
3. verfügbare Kernelmodule prüfen (`modinfo`/`lsmod`)
4. Firmwarefehler prüfen (`backend/core/firmware_resolver.py`)
5. installierte Paketinformationen prüfen
6. Distribution/Architektur berücksichtigen
7. kuratierte Quirks anwenden (`hardware_compat_catalog.py`)
8. sicheren Aktivierungsplan erzeugen (`driver_activation_plan.py`)

Jede Stufe kann früh mit `unknown` bzw. `review_required` enden, wenn die
Datenlage nicht ausreicht — es wird **nicht geraten**.

## DriverPlan

`live_activation_possible` und `persistent_install_possible` sind reine
Bewertungsfelder — kein Modul setzt sie in eine tatsächliche Aktion um.

## Paketquellen-Vertrauensstufen

1. bereits im Rescue-Image enthalten
2. offizielle Distribution-Repositories
3. signierter Setuphelfer-Offline-Cache
4. offizielles Herstellerrepository
5. manuell bereitgestelltes, signiertes Paket
6. unbekannte Quelle → **blockiert**

## Explizit verboten

- ungeprüfte Hersteller-Shellskripte (`curl|bash`)
- Download ohne Prüfsumme oder ohne TLS
- automatisches Hinzufügen von Paketquellen
- automatisches Akzeptieren von Lizenzbedingungen
- automatische Installation proprietärer Grafiktreiber
- dauerhafte Kernelmodul-Blacklists
- Secure-Boot-/MOK-Schlüsseländerung

## Firmware-Resolver (`backend/core/firmware_resolver.py`)

Firmwarestatus wird **getrennt** vom Treiberstatus bewertet
(`present|missing|unknown|not_required`). Ein geladener Treiber ohne passende
Firmware gilt als `firmware_missing`, nicht als `ready`.
