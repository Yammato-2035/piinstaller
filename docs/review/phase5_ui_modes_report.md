# Phase 5 – Aufteilung Grundlagen / Erweiterte Funktionen

_Datum: 2026-03-09_

## Abschlussbericht

### 1. Anzahl Funktionen pro Bereich

| Bereich | Anzahl Seiten/Funktionen |
|---------|--------------------------|
| **Grundlagen** | 10 (Dashboard, Assistent, Voreinstellungen, Einstellungen, Sicherheit, Benutzer, Backup, App Store, Update, ggf. DSI-Radio) |
| **Erweiterte Funktionen** | 14 (Remote, Dev, Webserver, Mail, NAS, Hausautomation, Musikbox, Kino, Lerncomputer, Monitoring, Control Center, Peripherie-Scan, Raspberry Pi Config, ggf. DSI-Radio) |
| **Diagnose** | 3 (Einstellungen/Logs, Monitoring, Peripherie-Scan) |

*Überlappung: Einige Seiten erscheinen in mehreren Modi (z. B. Settings in Grundlagen und Diagnose).*

---

### 2. Bereiche mit größter Vereinfachung

- **Grundlagen-Modus:** Reduzierung von ~24 auf ~10 sichtbare Menüpunkte für Einsteiger.
- **Control Center:** Performance, ASUS-ROG-Lüfter, Corsair/RGB standardmäßig ausgeblendet, per Toggle einblendbar.
- **Diagnose-Modus:** Bündelung von Logs, Monitoring und Peripherie-Scan an einem Ort.

---

### 3. Bereiche mit größter Expertenlogik

- **Erweiterte Funktionen:** Remote Companion, Control Center (inkl. Performance, Lüfter, RGB), Raspberry Pi Config, Peripherie-Scan.
- **Diagnose:** Monitoring, Peripherie-Scan, Einstellungen → Logs.

---

### 4. Die 10 wichtigsten UX-Verbesserungen

1. **Modus-Tabs** in der Sidebar: Grundlagen | Erweitert | Diagnose.
2. **Grundlagen reduziert** auf 10 zentrale Funktionen.
3. **Erweiterte Funktionen** klar gruppiert und erreichbar.
4. **Diagnose-Bereich** für Fehlersuche und Systemanalyse.
5. **Control Center:** Toggle „Erweiterte Optionen“ für Performance/Lüfter/RGB.
6. **Modus-Persistenz** in localStorage – Nutzer-Präferenz bleibt erhalten.
7. **Keine Funktion verloren** – alles über Modus-Wechsel erreichbar.
8. **Dokumentation** im Footer weiterhin immer sichtbar.
9. **ui_modes.md** dokumentiert Klassifizierung und Entscheidungsregeln.
10. **Konsistenz** mit Settings-Seite (bereits vorhandener „Erweiterte Einstellungen“-Toggle).

---

### 5. Validierung

- Anwendung startet
- Navigation funktioniert
- Keine toten Links
- Alle Funktionen über Modus-Wechsel erreichbar
- Dokumentation und Beenden im Footer unverändert
