# Backup & Restore Sicherheitsregeln

## Ziel
Backup- und Restore-Funktionalität darf niemals zu Datenverlust, Systembeschädigung oder Sicherheitslücken führen.

---

## VERBOTEN

- Restore außerhalb definierter erlaubter Pfade
- Überschreiben von Systempfaden (/etc, /usr, /boot, /var) ohne explizite Freigabe
- Nutzung relativer Pfade ohne Normalisierung
- Nutzung von Symlinks im Backup ohne Prüfung
- Restore ohne vorherige Validierung

---

## PFLICHTPRÜFUNGEN (VOR RESTORE)

1. Pfadnormalisierung
   - Nutzung von realpath
   - Vergleich mit erlaubten Basisverzeichnissen

2. Symlink-Schutz
   - Symlinks erkennen
   - optional blockieren oder explizit erlauben

3. Zielprüfung
   - Zielverzeichnis existiert
   - Schreibrechte vorhanden
   - kein kritischer Systempfad

4. Backup-Validität
   - Struktur vorhanden
   - erwartete Dateien vorhanden

---

## OPTIONAL (EMPFOHLEN)

- SHA256 Hash prüfen
- Backup-Größe validieren
- Dateitypen whitelisten

---

## FEHLERBEHANDLUNG

Bei Verstoß:
- sofort abbrechen
- klaren Fehler zurückgeben
- keine Teiloperationen

---

## STATUSLOGIK

Wenn Sicherheitsprüfung nicht vollständig:
→ Ampel mindestens GELB

Wenn kritische Risiken:
→ Ampel ROT

