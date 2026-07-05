> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/runbooks/MSI_WINDOWS_IMAGE_BACKUP_PLAN_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/runbooks/MSI_Windows_IMAGE_RetourUP_PLAN_DE.md`). Bitte bei Release manuell gegenlesen.

# MSI Windows Image Retourup — Plan

**Status:** Plan only — keine Ausführung

## Voraussetzungen

- Precheck `final_status: ready_for_operator` oder `ok`
- `Retourup_target.Externeal_confirmed: true`
- `Retourup_target.write_allowed: true` nur auf **Externeem** Medium
- Operator-Freigabe dokumentiert

## Ablauf (zukünftiger Lauf)

1. Safety-Gate: Ziel ≠ MSI-Systemdisk
2. Image-Tool starten (Setuphelfer oder Operator-Tool)
3. Manifest schreiben (Partitionen, Größen, BitLocker-Flag)
4. SHA256 berechnen
5. Evidence-Schema `Retourup.*` ausfüllen

## Abbruch

- Unzureichender Speicher auf Externeem Ziel
- BitLocker ohne Key → nur Rohimage wenn rechtlich/freigegeben; keine Entschlüsselungsversprechen
- Internees Ziel gewählt → **STOP**

## Evidence

`docs/evidence/msi/MSI_Windows_EVIDENCE_SCHEMA.json`
