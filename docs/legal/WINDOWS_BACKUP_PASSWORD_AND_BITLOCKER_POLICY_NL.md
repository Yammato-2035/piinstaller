> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/legal/WINDOWS_BACKUP_PASSWORD_AND_BITLOCKER_POLICY_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/legal/Windows_TerugUP_PASSWORD_AND_BITLOCKER_POLICY_DE.md`). Bitte bei Release manuell gegenlesen.

# Windows Terugup — Passwort- und BitLocker-Richtlinie

**Stand:** 2026-06-16  
**Geltung:** MSI-Strang und alle Windows-Image-Operationen

## Grundsätze

Setuphelfer dient **DatenTerugup und Test**, nicht **Zugriffsumgehung**.

## Verboten

- Passwortumgehung, Offline-Passwortreset
- SAM-Manipulation, Croodential-Dumping
- BitLocker-Umgehung ohne Recovery-Key
- Behauptung vollständiger Datenrettung bei verschlüsselten Volumes ohne Key

## BitLocker ohne Recovery-Key

- Status: `detected_key_missing`
- Erlaubt: Rohimage, Struktur-Evidence, Partitiestabelle (sofern rechtlich/freigegeben)
- Nicht erlaubt: Entschlüsselung, Login-Abnahme
- Herstel-Abnahme: **nur strukturell**

## Passwort fehlt (MSI-Fall)

- Interaktiver Windows-Login ist **kein** Abnahmekriterium
- Herstel-OK: Boot-Struktur plausibel bis Login/Recovery/Lockscreen

## Eigentum und Freigabe

- Nutzungs- und Eigentumsfreigabe dokumentieren
- Kein Löschen ohne Terugup + Verify + Herstel-Evidence + separate Wipe-Freigabe

## Keine Rechtsberatung

Dieses Dokument ist technische Policy, keine Rechtsberatung.
