# Driver & Firmware Resolution Architecture — PI-RS-HW-COMPAT-PROVISION-001

Stand: Phase 19. Beschreibt die Resolver-Pipeline, die aus Rohdaten der
Hardware-Inventur (siehe `HARDWARE_DETECTION_ARCHITECTURE.md`) einen
**Vorschlag** für Treiber-/Firmwareaktivierung erzeugt — ohne diesen
auszuführen.

## Resolver-Stufen (`backend/core/driver_resolver.py`)

```
1. Kernel-Modalias auswerten
2. gebundenen Treiber prüfen (kernel_driver_in_use)
3. verfügbare Kernelmodule prüfen (modinfo/lsmod)
4. Firmwarefehler prüfen (backend/core/firmware_resolver.py, dmesg-Muster)
5. installierte Paketinformationen prüfen
6. Distribution/Architektur berücksichtigen
7. kuratierte Quirks anwenden (backend/core/hardware_compat_catalog.py)
8. sicheren Aktivierungsplan erzeugen (backend/core/driver_activation_plan.py)
```

Jede Stufe kann früh mit `unknown` bzw. `review_required` enden, wenn die
Datenlage nicht ausreicht — es wird **nicht geraten**.

## `DriverPlan`-Contract

Das Ergebnis jeder Anfrage ist ein reiner Vorschau-Datensatz:

```json
{
  "device_id": "...",
  "current_state": "...",
  "recommended_driver": "...",
  "alternative_drivers": [],
  "driver_type": "kernel_in_tree|userspace|firmware_only|proprietary_optional|unsupported",
  "package_candidates": [],
  "firmware_candidates": [],
  "kernel_compatible": true,
  "secure_boot_impact": "none|review_required|blocking",
  "license_review_required": false,
  "network_required": false,
  "reboot_required": false,
  "live_activation_possible": false,
  "persistent_install_possible": false,
  "rollback_plan": {},
  "warnings": [],
  "errors": []
}
```

`live_activation_possible` und `persistent_install_possible` sind reine
**Bewertungsfelder** dieser Phase — kein Modul in diesem Repository setzt sie
in eine tatsächliche Aktion um.

## Paketquellen-Vertrauensstufen

Absteigend nach Vertrauen, aufsteigend nach Risiko:

1. bereits im Rescue-Image enthalten
2. offizielle Distribution-Repositories
3. signierter Setuphelfer-Offline-Cache
4. offizielles Herstellerrepository
5. manuell bereitgestelltes, signiertes Paket
6. unbekannte Quelle → **blockiert**

## Explizit verboten (diese und die aktuell aktive Phase)

- ungeprüfte Hersteller-Shellskripte (`curl|bash`, `wget|sh`)
- Download ohne Prüfsumme oder ohne TLS
- automatisches Hinzufügen von Paketquellen
- automatisches Akzeptieren von Lizenzbedingungen
- automatische Installation proprietärer Grafiktreiber
- dauerhafte Kernelmodul-Blacklists
- Secure-Boot-/MOK-Schlüsseländerung

`backend/core/driver_activation_plan.py` ist der einzige Ort, an dem ein
`DriverPlan` in einen „Aktivierungsplan" umgewandelt wird — und selbst dort
bleibt jede Aktion `preview_only`/`blocked`, niemals ausgeführt.

## Firmware-Resolver (`backend/core/firmware_resolver.py`)

Firmwarestatus wird **getrennt** vom Treiberstatus bewertet
(`present|missing|unknown|not_required`). Ein geladener Treiber ohne
passende Firmware gilt als `firmware_missing`, nicht als `ready`.

## Kuratierter Katalog als Quirk-Quelle

`backend/core/hardware_compat_catalog.py` liefert nur **belegte
Sonderfälle** (siehe `data/hardware/hardware_compat_catalog.json` und
`data/hardware/hardware_quirks.json`) — keine pauschale Regel für ganze
Geräteklassen. ASUS-/MSI-spezifische Erkenntnisse (z. B. Bootparameter aus
älteren Rescue-Retests) fließen ausschließlich als Katalogeinträge ein, nie
als generischer Code-Zweig.
