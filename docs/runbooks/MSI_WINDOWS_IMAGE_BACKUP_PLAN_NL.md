> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/runbooks/MSI_WINDOWS_IMAGE_BACKUP_PLAN_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/runbooks/MSI_Windows_IMAGE_TerugUP_PLAN_DE.md`). Bitte bei Release manuell gegenlesen.

# MSI Windows Image Terugup — Plan

**Status:** Plan only — keine Ausführung

## Voraussetzungen

- Precheck `final_status: ready_for_operator` oder `ok`
- `Terugup_target.External_confirmed: true`
- `Terugup_target.write_allowed: true` nur auf **Externem** Medium
- Operator-Freigabe dokumentiert

## Ablauf (zukünftiger Lauf)

1. Safety-Gate: Ziel ≠ MSI-Systemdisk
2. Image-Tool starten (Setuphelfer oder Operator-Tool)
3. Manifest schreiben (Partitieen, Größen, BitLocker-Flag)
4. SHA256 berechnen
5. Evidence-Schema `Terugup.*` ausfüllen

## Abbruch

- Unzureichender Speicher auf Externem Ziel
- BitLocker ohne Key → nur Rohimage wenn rechtlich/freigegeben; keine Entschlüsselungsversprechen
- Internes Ziel gewählt → **STOP**

## Evidence

`docs/evidence/msi/MSI_Windows_EVIDENCE_SCHEMA.json`
