# Windows Backup — Passwort- und BitLocker-Richtlinie

**Stand:** 2026-06-16  
**Geltung:** MSI-Strang und alle Windows-Image-Operationen

## Grundsätze

Setuphelfer dient **Datensicherung und Test**, nicht **Zugriffsumgehung**.

## Verboten

- Passwortumgehung, Offline-Passwortreset
- SAM-Manipulation, Credential-Dumping
- BitLocker-Umgehung ohne Recovery-Key
- Behauptung vollständiger Datenrettung bei verschlüsselten Volumes ohne Key

## BitLocker ohne Recovery-Key

- Status: `detected_key_missing`
- Erlaubt: Rohimage, Struktur-Evidence, Partitionstabelle (sofern rechtlich/freigegeben)
- Nicht erlaubt: Entschlüsselung, Login-Abnahme
- Restore-Abnahme: **nur strukturell**

## Passwort fehlt (MSI-Fall)

- Interaktiver Windows-Login ist **kein** Abnahmekriterium
- Restore-OK: Boot-Struktur plausibel bis Login/Recovery/Lockscreen

## Eigentum und Freigabe

- Nutzungs- und Eigentumsfreigabe dokumentieren
- Kein Löschen ohne Backup + Verify + Restore-Evidence + separate Wipe-Freigabe

## Keine Rechtsberatung

Dieses Dokument ist technische Policy, keine Rechtsberatung.
