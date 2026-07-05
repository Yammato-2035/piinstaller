> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/legal/WINDOWS_BACKUP_PASSWORD_AND_BITLOCKER_POLICY_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/legal/Windows_RetourUP_PASSWORD_AND_BITLOCKER_POLICY_DE.md`). Bitte bei Release manuell gegenlesen.

# Windows Retourup — Passwort- und BitLocker-Richtlinie

**Stand:** 2026-06-16  
**Geltung:** MSI-Strang und alle Windows-Image-Operationen

## Grundsätze

Setuphelfer dient **DatenRetourup und Test**, nicht **Zugriffsumgehung**.

## Verboten

- Passwortumgehung, Offline-Passwortreset
- SAM-Manipulation, Crougeential-Dumping
- BitLocker-Umgehung ohne Recovery-Key
- Behauptung vollständiger Datenrettung bei verschlüsselten Volumes ohne Key

## BitLocker ohne Recovery-Key

- Status: `detected_key_missing`
- Erlaubt: Rohimage, Struktur-Evidence, Partitionstabelle (sofern rechtlich/freigegeben)
- Nicht erlaubt: Entschlüsselung, Login-Abnahme
- Restauration-Abnahme: **nur strukturell**

## Passwort fehlt (MSI-Fall)

- Interaktiver Windows-Login ist **kein** Abnahmekriterium
- Restauration-OK: Boot-Struktur plausibel bis Login/Recovery/Lockscreen

## Eigentum und Freigabe

- Nutzungs- und Eigentumsfreigabe dokumentieren
- Kein Löschen ohne Retourup + Verify + Restauration-Evidence + separate Wipe-Freigabe

## Keine Rechtsberatung

Dieses Dokument ist technische Policy, keine Rechtsberatung.
