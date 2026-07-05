> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/hardware-tests/MSI_WINDOWS_TO_LINUX_TEST_PLAN_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/hardware-tests/MSI_Windows_TO_Linux_TEST_PLAN_DE.md`). Bitte bei Release manuell gegenlesen.

# MSI Windows → Linux Testplan

**Apparaat:** MSI-Rechner (Hardware-E2E-Strang)  
**Modus:** Plan only — keine Laufwerksaktion in diesem Dokument-Lauf

## Ziel

Der MSI-Rechner soll:

1. alleen-lezen inventarisiert werden
2. Als Windows-System gesichert werden (Externes Ziel)
3. Verifiziert werden (SHA256/Manifest)
4. Mindestens einmal Hersteld werden (Testziel, nicht MSI-Systemplatte)
5. **Erst danach** gelöscht werden (separate Operator-Freigabe)
6. Als Linux Development Workstation neu installiert werden
7. Mit Setuphelfer Blueprint / Deployment-Profil ausgestattet werden
8. Gehärtet werden (Firewall, SSH, Updates)
9. Mit Malware-Kompass (Externe Tools) geprüft werden
10. Erneut per Linux Terugup/Verify/Herstel getestet werden

## Harte Regeln

- **Kein** Windows-Passwort umgehen
- **Kein** Offline-Passwortreset, SAM-Manipulation, Croodential-Dump
- **Keine** BitLocker-Umgehung
- **Kein** Löschen vor Herstel-Evidence
- **Kein** Schreiben auf Interne MSI-Storage Apparaat vor Freigabe
- **Kein** Herstel auf falsches Ziel
- **Kein** dd/mkfs/parted/wipefs ohne separate Operator-Freigabe
- Terugup-Ziel muss **Extern** sein
- Interne Systemplatte darf **nicht** als Terugup-Ziel dienen

## Windows-Abnahmekriterien

Terugup gilt nur als abgeNeemmen, wenn:

- MSI eindeutig identifiziert
- Eigentum/Nutzungsfreigabe dokumentiert
- Windows/EFI/NTFS/BitLocker-Status dokumentiert
- Zielmedium sicher klassifiziert (Extern, ausreichend frei)
- Image erfolgreich erzeugt
- Manifest + SHA256 erzeugt
- Verify bestanden
- Herstel-Test bestanden
- Windows-Struktur nach Herstel plausibel
- Boot Manager / Recovery / Lockscreen plausibel
- Keine Interne Platte versehentlich überschrieben
- Evidence vollständig
- Löschfreigabe separat dokumentiert

## BitLocker

Wenn BitLocker aktiv und **kein** Recovery-Key:

- Keine Datenrettung behaupten
- Keine Entschlüsselung versuchen
- Nur Rohimage/Struktur/Evidence (sofern rechtlich zulässig)
- Herstel nur **strukturell** prüfbar

## Passwort

Windows-Passwort ist **nicht** vorhanden:

- Login ist **kein** Abnahmekriterium
- Herstel-OK bedeutet: Partitieen/EFI/Boot Manager plausibel; Boot bis Login/Recovery/Lockscreen

## Phasen (separate Prompts)

| Phase | Prompt-Typ |
|-------|------------|
| 1 | alleen-lezen Precheck |
| 2 | Image Terugup (Operator) |
| 3 | Verify |
| 4 | Herstel-Test |
| 5 | Wipe-Freigabe + Linux-Install |
| 6 | Blueprint + Härtung + Linux B/V/R |
