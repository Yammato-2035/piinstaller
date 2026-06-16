# MSI Windows → Linux Testplan

**Gerät:** MSI-Rechner (Hardware-E2E-Strang)  
**Modus:** Plan only — keine Laufwerksaktion in diesem Dokument-Lauf

## Ziel

Der MSI-Rechner soll:

1. Read-only inventarisiert werden
2. Als Windows-System gesichert werden (externes Ziel)
3. Verifiziert werden (SHA256/Manifest)
4. Mindestens einmal restored werden (Testziel, nicht MSI-Systemplatte)
5. **Erst danach** gelöscht werden (separate Operator-Freigabe)
6. Als Linux Development Workstation neu installiert werden
7. Mit Setuphelfer Blueprint / Deployment-Profil ausgestattet werden
8. Gehärtet werden (Firewall, SSH, Updates)
9. Mit Malware-Kompass (externe Tools) geprüft werden
10. Erneut per Linux Backup/Verify/Restore getestet werden

## Harte Regeln

- **Kein** Windows-Passwort umgehen
- **Kein** Offline-Passwortreset, SAM-Manipulation, Credential-Dump
- **Keine** BitLocker-Umgehung
- **Kein** Löschen vor Restore-Evidence
- **Kein** Schreiben auf interne MSI-Datenträger vor Freigabe
- **Kein** Restore auf falsches Ziel
- **Kein** dd/mkfs/parted/wipefs ohne separate Operator-Freigabe
- Backup-Ziel muss **extern** sein
- Interne Systemplatte darf **nicht** als Backup-Ziel dienen

## Windows-Abnahmekriterien

Backup gilt nur als abgenommen, wenn:

- MSI eindeutig identifiziert
- Eigentum/Nutzungsfreigabe dokumentiert
- Windows/EFI/NTFS/BitLocker-Status dokumentiert
- Zielmedium sicher klassifiziert (extern, ausreichend frei)
- Image erfolgreich erzeugt
- Manifest + SHA256 erzeugt
- Verify bestanden
- Restore-Test bestanden
- Windows-Struktur nach Restore plausibel
- Boot Manager / Recovery / Lockscreen plausibel
- Keine interne Platte versehentlich überschrieben
- Evidence vollständig
- Löschfreigabe separat dokumentiert

## BitLocker

Wenn BitLocker aktiv und **kein** Recovery-Key:

- Keine Datenrettung behaupten
- Keine Entschlüsselung versuchen
- Nur Rohimage/Struktur/Evidence (sofern rechtlich zulässig)
- Restore nur **strukturell** prüfbar

## Passwort

Windows-Passwort ist **nicht** vorhanden:

- Login ist **kein** Abnahmekriterium
- Restore-OK bedeutet: Partitionen/EFI/Boot Manager plausibel; Boot bis Login/Recovery/Lockscreen

## Phasen (separate Prompts)

| Phase | Prompt-Typ |
|-------|------------|
| 1 | Read-only Precheck |
| 2 | Image Backup (Operator) |
| 3 | Verify |
| 4 | Restore-Test |
| 5 | Wipe-Freigabe + Linux-Install |
| 6 | Blueprint + Härtung + Linux B/V/R |
