# PI-RS-USB-MSI-GUI-002 — Ergebnis

Stand: 2026-07-12  
HEAD: `f116f895` (vor Commit)

## USB-Update

| Feld | Wert |
|------|------|
| Gerät | Intenso Ultra Line, 59G, `/dev/sda` |
| Alte Payload-Version (Stick-Metadaten) | **1.10.0.13** (tatsächlich gemessen; Brief nannte 1.10.0.14) |
| Neue Payload-Version | **1.10.0.15** |
| Erwarteter SHA256 | `307ae9a381e2792fddd2ca8ebb6c20550544f0b167e2461c323c596651ecd318` |
| Tatsächlicher SHA256 (Stick) | identisch |
| Updateweg | `scripts/rescue-live/update-fat32-esp-live-payload.sh` |
| Partitionstabelle | unverändert |
| SETUP_LOGS | erhalten |

## Gates vor/nach Update

- `check-rescue-payload-msi-gui002-content.sh`: **ok** (Build-Artefakt + Stick-SquashFS)
- `check-rescue-payload-no-secrets.sh`: **ok**
- PI-RS-MSI-GUI-002 pytest: **19 passed**

## MSI-Boot-Retest

**Nicht in diesem Agent-Lauf durchgeführt** — physischer Operator-Boot auf GE63 erforderlich.

Letzte SETUP_LOGS-Session (`20260712_015835`) stammt von **vor** dem 1.10.0.15-Update und dient nicht als Abnahme für diesen Sprint.

## Korrekte Aussage (Ziel nach bestandenem Test)

Unter dem MSI-Kompatibilitätsprofil wird die grafische Oberfläche kontrolliert deaktiviert. Die Textoberfläche bleibt auf dem MSI GE63 stabil und bedienbar.

**Nicht** behaupten: „GUI funktioniert auf MSI“.

## Verbleibende Risiken

- `version.json`-Updater behält initial alte `project_version`; manuell auf 1.10.0.15 synchronisiert
- Physischer Boot-Retest ausstehend
- `filesystem.squashfs.prev-1.10.0.4` auf ESP belassen (etablierter Updater-Pfad)

## Nächster Schritt

**PI-RS-MSI-RETEST-002** — MSI GE63 Operator Boot Retest mit Payload 1.10.0.15

Alternativ nach E2E-Nachweis:

**PI-RS-TEL-LIVE-001** oder **CSE-INCOMING-TEL-001**
