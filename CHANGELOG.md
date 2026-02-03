# Changelog

Alle wichtigen Änderungen am PI-Installer werden hier dokumentiert.  
Details und Versionsschema: [VERSIONING.md](./VERSIONING.md).

---

## [1.2.0.3] – 2026-02

### Mixer-Installation

- **Backend:** Update und Install in zwei Schritten (`apt-get update`, dann `apt-get install`); Dpkg-Optionen `--force-confdef`/`--force-confold` für nicht-interaktive Installation; bei Fehler wird `copyable_command` zurückgegeben; Timeout-Meldung klarer.
- **Frontend (Musikbox & Kino/Streaming):** Bei Fehler erscheint unter den Mixer-Buttons ein Hinweis „Installation fehlgeschlagen. Manuell im Terminal ausführen:“ mit Befehl und **Kopieren**-Button.

---

## [1.2.0.2] – 2026-02

### Geändert

- **Dashboard – Hardware & Sensoren:** Bereich „Systeminformationen“ entfernt (ist bereits in der Übersicht sichtbar).
- **CPU & Grafik:** Treiber-Hinweise (NVIDIA/AMD/Intel) werden nicht mehr unter der CPU angezeigt, sondern unter der jeweiligen Grafikkarte (iGPU bzw. diskret).

### Dokumentation

- In der Anzeige (Dokumentation → Versionen & Changelog) nur die Endversion mit Details; ältere Updates kompakt bzw. überspringbar.

---

## [1.2.0.1] – 2026-02

### Behoben

- **Dashboard – IP-Adressen:** Text unter den IPs („Mit dieser IP von anderen Geräten erreichbar…“) war anthrazit und bei Hover unleserlich → jetzt `text-slate-200` und Link `text-sky-200`.
- **Dashboard – Updates:** Zeile „X Notwendig · Y Optional“ war zu blass → jetzt `text-slate-200` / `text-slate-100` für bessere Lesbarkeit.
- **Dashboard – Menü:** Buttons „Übersicht“, „Auslastung & Grafik“, „Hardware & Sensoren“ – inaktive Buttons hatten fast gleiche Farbe wie Schrift → jetzt `text-slate-200`, `bg-slate-700/70`, Hover `bg-slate-600`.
- **CPU & Grafik:** Es wurden 32 „Prozessoren“ (Threads) gelistet → ersetzt durch **eine** CPU-Zusammenfassung: Name, Kerne, Threads, Cache (L1–L3), Befehlssätze (aufklappbar), Chipsatz/Mainboard; integrierte Grafik und Grafikkarte unverändert; Auslastung nur noch physikalische Kerne (keine Thread-Liste).
- **Mixer-Installation:** Installation schlug weiterhin fehl → Sudo-Passwort wird getrimmt; `apt-get update -qq` vor install; `DEBIAN_FRONTEND=noninteractive` für update und install; Timeout 180s; Fehlermeldung bis 600 Zeichen; Logging bei Fehler.

### Backend

- `get_cpu_summary()`: Liest aus /proc/cpuinfo und lscpu Name, Kerne, Threads, Cache (L1–L3), Befehlssätze (flags).
- System-Info liefert `cpu_summary`; `hardware.cpus` wird auf einen Eintrag reduziert (keine Liste aller Threads).

---

## [1.2.0.0] – 2026-02

### Neu

- **Musikbox fertig:** Musikbox-Bereich abgeschlossen – Mixer-Buttons (pavucontrol/qpwgraph), Installation der Mixer-Programme per Knopfdruck (pavucontrol & qpwgraph), Sudo-Modal für Mixer-Installation.
- **Mixer:** Mixer in Musikbox und Kino/Streaming eingebaut – „Mixer öffnen (pavucontrol)“ / „Mixer öffnen (qpwgraph)“ starten die GUI-Mixer; „Mixer-Programme installieren“ installiert pavucontrol und qpwgraph per apt; Backend setzt `DISPLAY=:0` für GUI-Start; Installation mit `DEBIAN_FRONTEND=noninteractive` für robuste apt-Installation.
- **Dashboard:** Erweiterungen und Quick-Links; Versionsnummer und Changelog auf 1.2.0.0 aktualisiert.

### API

- `POST /api/system/run-mixer` – Grafischen Mixer starten (Body: `{"app": "pavucontrol"}` oder `{"app": "qpwgraph"}`).
- `POST /api/system/install-mixer-packages` – pavucontrol und qpwgraph installieren (Body optional: `{"sudo_password": "..."}`).

### Dokumentation

- Changelog 1.2.0.0 in App (Dokumentation → Versionen & Changelog).
- Troubleshooting: Mixer-Installation fehlgeschlagen (manueller Befehl, Sudo, DISPLAY) in Dokumentation und INSTALL.md.
- INSTALL.md: API Mixer (run-mixer, install-mixer-packages); FEATURES.md: v1.2 Features; README Version 1.2.0.0.

---

## [1.0.4.0] – 2026-01

- Sicherheit-Anzeige im Dashboard (2/5 aktiviert bei Firewall + Fail2Ban).
- Dokumentation & Changelog aktualisiert.

---

Ältere Einträge siehe **Dokumentation** in der App (Versionen & Changelog).
