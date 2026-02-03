# PI-Installer – Versionsschema und -führung

## Versionsnummer (X.Y.Z.W)

Die Versionsnummer folgt dem Schema **X.Y.Z.W**:

| Teil | Bedeutung | Erhöhung bei |
|------|-----------|--------------|
| **X** | Hauptversion | Gravierende Änderungen, inkompatible Umbrüche |
| **Y** | Nebenversion | Größere Releases, strategische Erweiterungen |
| **Z** | Neue Features | **Wird erhöht, wenn ein neues Feature hinzukommt** (z. B. neuer Bereich wie Kino/Streaming, neue Hauptfunktion). W wird auf 0 gesetzt. |
| **W** | Patch | Bugfixes, kleine Ergänzungen, UI-Anpassungen, Dokumentation (ohne neues Feature) |

## Wann wird die Version erhöht?

Die Versionsnummer wird **bei jeder Änderung** angepasst:

- **Bugfix** → W erhöhen (z. B. 1.0.1.3 → 1.0.1.4)
- **Ergänzung** (kleine neue Option, neues Feld, neuer Hinweis, ohne neues Feature) → W erhöhen
- **Neues Feature** (neuer Bereich, neue Hauptfunktion, z. B. Kino/Streaming) → **Z erhöhen, W auf 0 setzen** (z. B. 1.0.1.17 → 1.0.2.0)
- **Dokumentations- oder Texte-Anpassung** (sofern inhaltlich relevant) → W erhöhen
- **Reine Refactorings ohne sichtbare Änderung** → optional W erhöhen, um den Stand nachvollziehbar zu machen

So bleibt jeder Stand (z. B. aus Git) einer konkreten Version zugeordnet.

### Eine Version pro Bereich / pro Änderung

- **Pro Bereich:** Jede vorgenommene Veränderung oder Fehlerbehebung **pro Bereich** (z. B. WLAN, Control Center – SSH/VNC, Display, Raspberry Pi Config) führt zu **einer** Erhöhung von W (Patch). Mehrere Änderungen im selben Bereich können in einer Version zusammengefasst werden; Änderungen in unterschiedlichen Bereichen werden getrennt versioniert (z. B. 1.0.1.6 WLAN, 1.0.1.7 Services, 1.0.1.8 Display).
- **Dokumentation:** Die Dokumentation (Changelog in der App, ggf. Troubleshooting, VERSIONING.md) wird **immer selbstständig** zu jeder Änderung ergänzt – inklusive neuer Changelog-Einträge und Versionsnummer.

## Wo wird die Version geführt?

- **Quelle der Wahrheit:** Datei `VERSION` im Projektroot (eine Zeile, z. B. `1.0.1.13`).
- **Backend:** Liest die Version aus `VERSION` (z. B. für `/api/version`).
- **Frontend:** `frontend/package.json` → Feld `version` (wird automatisch aus `VERSION` synchronisiert).
- **Tauri (Desktop-App):** `frontend/src-tauri/tauri.conf.json` → Feld `version` (wird automatisch aus `VERSION` synchronisiert).

**Automatische Synchronisation:** Das Skript `frontend/sync-version.js` liest `VERSION` und schreibt die Version in `package.json` und `tauri.conf.json`. Es wird bei **`npm run prebuild`** ausgeführt (z. B. vor `npm run build`). Manuell: `cd frontend && node sync-version.js`.

Nach einer Änderung (Versionsbump):

1. **Versionsnummer erhöhen** – entweder:
   - **Neues Feature (Z erhöhen):** `node scripts/bump-feature.js` (erhöht Z um 1, setzt W auf 0, führt sync-version aus), oder
   - **Patch/Bugfix (W erhöhen):** `node scripts/bump-version.js` (erhöht W um 1, führt sync-version aus), oder
   - **Manuell:** `VERSION` anpassen (z. B. 1.0.1.17 → 1.0.2.0 bei neuem Feature, 1.0.1.17 → 1.0.1.18 bei Patch), dann im Frontend: `npm run prebuild`.
2. **Changelog** in der App ergänzen: Dokumentation → Versionen & Changelog (in `frontend/src/pages/Documentation.tsx`).

## Changelog & Dokumentation

- Der Changelog wird in der **Dokumentation** der Anwendung geführt (Seite „Dokumentation“ → Kapitel „Versionen & Changelog“). Dort sind pro Version die Änderungen (Bugfixes, Ergänzungen, Features) kurz beschrieben.
- **Regel:** Zu jeder Änderung/Fehlerbehebung wird die Dokumentation **selbstständig** ergänzt: Versionsnummer erhöhen (pro Bereich), Changelog-Eintrag anlegen, ggf. Troubleshooting oder andere Kapitel anpassen.
- Für Releases kann zusätzlich eine Datei `CHANGELOG.md` im Root gepflegt werden (optional).

---

## Mehrere Entwickler (z. B. Laptop + Raspberry Pi)

Wenn **zwei (oder mehr) Personen** unabhängig arbeiten – z. B. **Volker auf dem Laptop**, **Gabriel auf dem Raspberry Pi** – können beide Änderungen zu GitHub hochladen. Wichtig: vor dem Hochladen immer die neuesten Änderungen der anderen holen.

### Unabhängig zu GitHub hochladen

- **Ja.** Beide können pushen – aber **nacheinander** und mit **Pull vor Push**, damit keine Konflikte entstehen:
  1. Vor dem ersten Push des Tages: `git pull origin main` (oder den genutzten Branch-Namen).
  2. Falls es Merge-Konflikte gibt: Konflikte auflösen, dann `git add` und `git commit`, danach `git push`.
  3. Der andere holt sich danach mit `git pull` die neuen Commits.

So können z. B. Volkers Änderungen (Laptop) und Gabriels Änderungen (Pi) unabhängig entstehen und nacheinander zu GitHub hochgeladen werden.

### Änderungen des anderen in Doku und Versionsnummer nachziehen

**Beispiel: Volker möchte Gabriels gestrige Änderungen in die Dokumentation und Versionskontrolle aufnehmen.**

1. **Gabriels Stand von GitHub holen**
   ```bash
   git pull origin main
   ```
   Damit sind Gabriels Commits (z. B. vom Pi) lokal auf deinem Laptop.

2. **Dokumentation ergänzen**
   - In der App: **Dokumentation** → **Versionen & Changelog** die neue Version (z. B. 1.0.1.5) eintragen und Gabriels Änderungen als Stichpunkte notieren.
   - Datei: `frontend/src/pages/Documentation.tsx` (Abschnitt „Versionen & Changelog“).

3. **Versionsnummer anheben** (falls für Gabriels Änderungen noch nicht geschehen)
   - `VERSION` im Projektroot anpassen (z. B. 1.0.1.4 → 1.0.1.5).
   - Im Frontend: `npm run prebuild` ausführen (synchronisiert package.json und tauri.conf.json aus VERSION).

4. **Commit und Push**
   ```bash
   git add VERSION frontend/package.json frontend/src-tauri/tauri.conf.json frontend/src/pages/Documentation.tsx
   git commit -m "Doku & Version: Gabriels Änderungen (z. B. 1.0.1.5) ergänzt"
   git push origin main
   ```

So kannst du (Volker) Gabriels bereits gepushte Änderungen einholen und die Dokumentation sowie die Versionsnummernkontrolle dafür ergänzen und selbst committen/pushen.
