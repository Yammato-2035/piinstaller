## Asset-System – Icons, Illustrationen & Website-Bezug

_Zweck: Entwickler-orientierte Zusammenfassung der Asset-Architektur._

---

### 1. Ziele des Asset-Systems

- Einheitliche Symbolsprache für:
  - App-UI (React/Tauri)
  - spätere Website/Doku
- Minimierung von Duplikaten:
  - Icons und Illustrationen sollen an einer Stelle gepflegt und von beiden Oberflächen genutzt werden.

---

### 2. Technische Grundlage

- **Quelle im Frontend**:
  - `frontend/public/assets/icons/**`
  - (geplante) `frontend/public/assets/illustrations/**`
  - (geplante) `frontend/public/assets/website/**`

- **Build-Ausgabe**:
  - `frontend/dist/assets/icons/**` – deployte Icons.
  - `frontend/dist/docs/screenshots/README.md` – Hinweis auf Screenshots (nicht vollständig im Repo).

- **AppIcon-Komponente**:
  - `frontend/src/components/AppIcon.tsx` mappt:
    - `navigation` → `navigation/icon_*.svg`
    - `status` → `status/status_*.svg`
    - `devices` → `devices/device_*.svg`
    - `process` → `process/process_*.svg`
    - `diagnostic` → `diagnostic/diagnose_*.svg`

- **Lucide-Icons**:
  - `lucide-react` als Ergänzung für Inline-Icons (CPU, Festplatte, Cloud, etc.).

---

### 3. Kategorien & Beispiele

Siehe auch `docs/design/asset_inventory_complete.md`:

- Navigation:
  - Dashboard, Installation, Storage, Settings, Help, Diagnose, Advanced, Modules.
- Status:
  - OK, Warnung, Fehler, Läuft, Aktiv, Abgeschlossen, Update.
- Devices:
  - Raspberry Pi, SD-Karte, NVMe, USB, Netzwerk, WLAN, Ethernet, Display, Audio.
- Process:
  - Search, Connect, Prepare, Write, Verify, Restart, Complete.
- Diagnostic:
  - Error, Logs, Systemcheck, Debug, Test.

---

### 4. Website-Integration (geplant)

Dokumentiert in `docs/website/asset_reuse_plan.md`:

- Icons aus `assets/icons/` sollen 1:1 für Website-Darstellungen genutzt werden.
- Illustrationen:
  - `illustrations/install/`, `illustrations/connect/`, `illustrations/diagnose/`, `illustrations/empty_states/`
- Website-spezifische Assets:
  - `website/hero/`, `website/sections/`, `website/screenshots/`

> Implementierung dieser Struktur erfolgt bewusst **nicht** in dieser Konsolidierungsphase – nur Dokumentation.

---

### 5. Offene technische Fragen

1. **Master-Quelle für SVGs**:
   - Muss für zukünftige Arbeiten klar definiert werden (z. B. ausschließlich `frontend/public/assets/`).

2. **Umgang mit Screenshots**:
   - Aktuelle Doku referenziert `docs/screenshots/…`.
   - Für Website + App sollte es eine zentrale, kuratierte Screenshot-Sammlung geben.

3. **Reduktion paralleler Icon-Systeme**:
   - Langfristig ist zu entscheiden, ob Lucide-Icons nur ergänzend oder als gleichberechtigtes System bestehen bleiben.

---

### 6. Selbstprüfung (Phase 9 – Asset-System)

- **Nur beschrieben, nicht umgesetzt?** – Ja, das Dokument fasst existierende Architektur- und Design-Dokumente zusammen.
- **Keine neuen Assets/Strukturen angelegt?** – Ja, es wurden nur Zielpfade textuell festgehalten.

