# MSI Windows Image Backup — Plan

**Status:** Plan only — keine Ausführung

## Voraussetzungen

- Precheck `final_status: ready_for_operator` oder `ok`
- `backup_target.external_confirmed: true`
- `backup_target.write_allowed: true` nur auf **externem** Medium
- Operator-Freigabe dokumentiert

## Ablauf (zukünftiger Lauf)

1. Safety-Gate: Ziel ≠ MSI-Systemdisk
2. Image-Tool starten (Setuphelfer oder Operator-Tool)
3. Manifest schreiben (Partitionen, Größen, BitLocker-Flag)
4. SHA256 berechnen
5. Evidence-Schema `backup.*` ausfüllen

## Abbruch

- Unzureichender Speicher auf externem Ziel
- BitLocker ohne Key → nur Rohimage wenn rechtlich/freigegeben; keine Entschlüsselungsversprechen
- Internes Ziel gewählt → **STOP**

## Evidence

`docs/evidence/msi/MSI_WINDOWS_EVIDENCE_SCHEMA.json`
