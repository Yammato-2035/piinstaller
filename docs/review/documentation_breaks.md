## Dokumentationsbrüche & zentrale Verweiskonflikte (Priorität A)

_Stand: März 2026 – nur harte Brüche und irreführende Verweise._

---

### DB‑A1 – README vs. tatsächliche Doku‑Struktur

- **Beobachtung**:
  - `README.md` (Abschnitte „📚 Dokumentation“, „🏗️ Projektstruktur“, „🌟 Status“) referenziert:
    - `./INSTALL.md`
    - `./ARCHITECTURE.md`
    - `./FEATURES.md`
    - `./SUGGESTIONS.md`
    - `./VERSIONING.md`
    - `./README_remote_architecture.md`
    - sowie eine Root‑Struktur, in der diese Dateien im Projekt‑Root liegen.
  - Tatsächlich liegen die Dokumente inzwischen unter:
    - `docs/user/INSTALL.md`
    - `docs/architecture/ARCHITECTURE.md`
    - `docs/architecture/FEATURES.md`
    - `docs/architecture/SUGGESTIONS.md`
    - `docs/developer/VERSIONING.md`
    - `docs/developer/README_remote_architecture.md`
- **Risiko**:
  - GitHub‑Leser erhalten 404‑Links bzw. veraltete Strukturinformationen.
- **Minimale Maßnahme (empfohlen)**:
  - README‑Links auf die neuen Pfade unter `docs/…` umstellen.
  - Projektstruktur‑Block so anpassen, dass er _nur_ reale Dateien im Root nennt und bei Doku auf `docs/…` verweist.
- **Codeänderung nötig?**: Nein.

---

### DB‑A2 – SYSTEM_INSTALLATION.md: Verweis auf alte INSTALL.md‑Position

- **Beobachtung**:
  - `docs/SYSTEM_INSTALLATION.md` verweist (mindestens an einer Stelle) auf `../INSTALL.md`.
  - Die Installationsanleitung liegt inzwischen unter `docs/user/INSTALL.md`.
- **Risiko**:
  - Leser der System‑Installationsdoku landen beim „weiterführenden Link“ auf einer nicht existenten Datei.
- **Minimale Maßnahme (empfohlen)**:
  - Pfad auf `./user/INSTALL.md` oder relative korrekte Referenz anpassen.
- **Codeänderung nötig?**: Nein.

---

### DB‑A3 – QUICKSTART & weitere Docs mit INSTALL.md‑Rootverweis

- **Beobachtung**:
  - `docs/user/QUICKSTART.md` verweist auf eine INSTALL.md im selben Verzeichnis oder im Root, während die tatsächliche Datei unter `docs/user/INSTALL.md` liegt.
  - Weitere Dokumente (`docs/SICHERE_DEFAULTS.md`, `docs/ANALYSE_HUERDEN.md`, `docs/INSTALLATION_PI5.md` etc.) referenzieren `INSTALL.md` teils mit Pfaden, die nicht mehr mit der neuen Struktur übereinstimmen.
- **Risiko**:
  - Leser folgen innerhalb der Doku falschen oder stumpfen Verweisen.
- **Minimale Maßnahme (empfohlen)**:
  - Alle direkten INSTALL‑Verweise in diesen Kern‑Docs auf die konsistente Struktur unter `docs/user/` prüfen und korrigieren.
- **Codeänderung nötig?**: Nein.

---

### DB‑A4 – VERSION / VERSIONING vs. config/version.json (zentraler Bruch)

- **Beobachtung**:
  - Mehrere zentrale Dokumente (`README.md`, `CHANGELOG.md`, `docs/developer/VERSIONING.md`, `docs/developer/WORKFLOW_LAPTOP_PI.md`, diverse Packaging‑Docs) deklarieren `VERSION` im Projekt‑Root als führende Versionsquelle.
  - Im aktuellen Repo existiert zusätzlich `config/version.json`, ohne dass in der Doku klar beschrieben ist, wie sich beide Quellen zueinander verhalten.
- **Risiko**:
  - Entwickler wissen nicht, welche Datei für neue Releases maßgeblich ist.
  - Tools/Skripte könnten sich auf unterschiedliche Quellen beziehen.
- **Minimale Maßnahme (empfohlen)**:
  - Kurzfristig: README und `docs/developer/VERSIONING.md` um einen Abschnitt ergänzen, der den Status von `config/version.json` erklärt (z. B. „neues zentrales Format“, „wird schrittweise eingeführt“).
  - Keine sofortige Umstellung des Release‑Prozesses in dieser Phase.
- **Codeänderung nötig?**: Nein (Phase 1 bleibt bei Doku‑Korrektur).

---

### DB‑A5 – Screenshots‑Pfad (SYSTEM_AUDIT_REPORT.md)

- **Beobachtung**:
  - `docs/SYSTEM_AUDIT_REPORT.md` dokumentiert, dass `Documentation.tsx`, `README.md`, `INSTALL.md`, `QUICKSTART.md` auf `docs/screenshots/*.png` verweisen, der Ordner aber im Repo nicht vorhanden ist.
  - Aktuell zeigt `README.md` weiterhin auf `docs/screenshots/screenshot-*.png`.
- **Risiko**:
  - Zentrale Screenshots fehlen → UI‑Darstellung in der Doku bricht.
- **Minimale Maßnahme (empfohlen)**:
  - Kurzfristig im README darauf hinweisen, dass Screenshots (noch) nicht im Repo gebündelt sind, oder die Referenzen entfernen/neutralisieren.
  - Spätere Phase: Asset‑Strategie in den Design‑Docs (Phase 2).
- **Codeänderung nötig?**: Nein.

