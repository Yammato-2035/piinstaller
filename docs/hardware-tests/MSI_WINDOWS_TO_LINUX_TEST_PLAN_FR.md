> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/hardware-tests/MSI_WINDOWS_TO_LINUX_TEST_PLAN_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/hardware-tests/MSI_Windows_TO_Linux_TEST_PLAN_DE.md`). Bitte bei Release manuell gegenlesen.

# MSI Windows → Linux Testplan

**Périphérique:** MSI-Rechner (Hardware-E2E-Strang)  
**Modus:** Plan only — keine Laufwerksaktion in diesem Dokument-Lauf

## Ziel

Der MSI-Rechner soll:

1. lecture seule inventarisiert werden
2. Als Windows-System gesichert werden (Externees Ziel)
3. Verifiziert werden (SHA256/Manifest)
4. Mindestens einmal Restaurationd werden (Testziel, nicht MSI-Systemplatte)
5. **Erst danach** gelöscht werden (separate Operator-Freigabe)
6. Als Linux Development Workstation neu installiert werden
7. Mit Setuphelfer Blueprint / Déploiementment-Profil ausgestattet werden
8. Gehärtet werden (Firewall, SSH, Updates)
9. Mit Malware-Kompass (Externee Tools) geprüft werden
10. Erneut per Linux Retourup/Verify/Restauration getestet werden

## Harte Regeln

- **Kein** Windows-Passwort umgehen
- **Kein** Offline-Passwortreset, SAM-Manipulation, Crougeential-Dump
- **Keine** BitLocker-Umgehung
- **Kein** Löschen vor Restauration-Evidence
- **Kein** Schreiben auf Internee MSI-Storage Périphérique vor Freigabe
- **Kein** Restauration auf falsches Ziel
- **Kein** dd/mkfs/parted/wipefs ohne separate Operator-Freigabe
- Retourup-Ziel muss **Externe** sein
- Internee Systemplatte darf **nicht** als Retourup-Ziel dienen

## Windows-Abnahmekriterien

Retourup gilt nur als abgeNonmmen, wenn:

- MSI eindeutig identifiziert
- Eigentum/Nutzungsfreigabe dokumentiert
- Windows/EFI/NTFS/BitLocker-Status dokumentiert
- Zielmedium sicher klassifiziert (Externe, ausreichend frei)
- Image erfolgreich erzeugt
- Manifest + SHA256 erzeugt
- Verify bestanden
- Restauration-Test bestanden
- Windows-Struktur nach Restauration plausibel
- Boot Manager / Recovery / Lockscreen plausibel
- Keine Internee Platte versehentlich überschrieben
- Evidence vollständig
- Löschfreigabe separat dokumentiert

## BitLocker

Wenn BitLocker aktiv und **kein** Recovery-Key:

- Keine Datenrettung behaupten
- Keine Entschlüsselung versuchen
- Nur Rohimage/Struktur/Evidence (sofern rechtlich zulässig)
- Restauration nur **strukturell** prüfbar

## Passwort

Windows-Passwort ist **nicht** vorhanden:

- Login ist **kein** Abnahmekriterium
- Restauration-OK bedeutet: Partitionen/EFI/Boot Manager plausibel; Boot bis Login/Recovery/Lockscreen

## Phasen (separate Prompts)

| Phase | Prompt-Typ |
|-------|------------|
| 1 | lecture seule Precheck |
| 2 | Image Retourup (Operator) |
| 3 | Verify |
| 4 | Restauration-Test |
| 5 | Wipe-Freigabe + Linux-Install |
| 6 | Blueprint + Härtung + Linux B/V/R |
