# Rescue-Entscheidungslogik (Dry-Run) und Zielidentität

## Dry-Run-Entscheidung

Die Ampel (`restore_risk_level`), `restore_decision` und Blocker werden in `modules/rescue_restore_dryrun.py` aus Backup-Klasse, Sandbox-Status, Boot-Heuristik, Kapazität und SMART abgeleitet (`detect_restore_blockers`, `_compute_decision`).

## Zielidentität (Phase 3.N2)

Nachschärfung: Blockgeräte werden nicht nur per Pfad verglichen. Im Grant liegt `target_device_identity` (Modell, Seriennummer, UUID/PARTUUID, Größe, Transport), erzeugt durch `core/device_identity.build_device_identity`. Vor dem echten Restore wird die Identität erneut gemessen und mit `compare_device_identity` abgeglichen — Abweichung blockiert mit `rescue.hardstop.target_identity_mismatch`.

## Hinweis

Gerätenamen (`/dev/sdX`) können sich nach Neustart ändern; der Abgleich bevorzugt daher **stabile Felder** (Seriennummer, PARTUUID), fällt bei fehlenden Daten auf Größe + Modell + Pfad zurück (`weak_identity`).
