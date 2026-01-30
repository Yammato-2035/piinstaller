# PI-Installer – Versionsschema und -führung

## Versionsnummer (X.Y.Z.W)

Die Versionsnummer folgt dem Schema **X.Y.Z.W**:

| Teil | Bedeutung | Erhöhung bei |
|------|-----------|--------------|
| **X** | Hauptversion | Gravierende Änderungen, inkompatible Umbrüche |
| **Y** | Nebenversion | Neue Funktionen, größere Features |
| **Z** | Modul/Release | Bereich oder Modul abgeschlossen |
| **W** | Patch | Bugfixes, kleine Ergänzungen, UI-Anpassungen, Dokumentation |

## Wann wird die Version erhöht?

Die Versionsnummer wird **bei jeder Änderung** angepasst:

- **Bugfix** → W erhöhen (z. B. 1.0.1.3 → 1.0.1.4)
- **Ergänzung** (kleine neue Option, neues Feld, neuer Hinweis) → W erhöhen
- **Feature-Änderung** oder **Feature-Ergänzung** → Y oder Z erhöhen (je nach Umfang)
- **Dokumentations- oder Texte-Anpassung** (sofern inhaltlich relevant) → W erhöhen
- **Reine Refactorings ohne sichtbare Änderung** → optional W erhöhen, um den Stand nachvollziehbar zu machen

So bleibt jeder Stand (z. B. aus Git) einer konkreten Version zugeordnet.

### Empfehlung: Eine Version pro logischer Änderung

Statt für **jede** kleine Zeilenänderung W zu erhöhen, kann man **eine Versionserhöhung pro logischer Änderung oder pro abgeschlossenem Arbeitsschritt** vornehmen (z. B. ein Bugfix, eine Doku-Ergänzung, ein kleines Feature). Mehrere zusammengehörige Anpassungen (z. B. „Dokumentation auf Stand bringen“ inkl. Changelog und Troubleshooting) können als **eine** Version (z. B. 1.0.1.5) erfasst werden. Das hält den Changelog übersichtlich und bleibt mit dem Schema X.Y.Z.W kompatibel.

## Wo wird die Version geführt?

- **Quelle der Wahrheit:** Datei `VERSION` im Projektroot (eine Zeile, z. B. `1.0.1.4`).
- **Backend:** Liest die Version aus `VERSION` (z. B. für `/api/version`).
- **Frontend:** `frontend/package.json` → Feld `version` (wird per `npm run prebuild` aus `VERSION` synchronisiert, siehe `frontend/sync-version.js`).
- **Tauri (Desktop-App):** `frontend/src-tauri/tauri.conf.json` → Feld `version` (bei Release manuell an `VERSION` anpassen).

Nach einer Änderung von `VERSION`:

1. `VERSION` anpassen.
2. Im Frontend: `npm run prebuild` ausführen (oder `version` in `package.json` von Hand anpassen).
3. Tauri: `version` in `tauri.conf.json` ggf. anpassen.
4. Changelog in der Dokumentation (z. B. unter „Versionen & Changelog“ in der App) ergänzen.

## Changelog

Der Changelog wird in der **Dokumentation** der Anwendung geführt (Seite „Dokumentation“ → Kapitel „Versionen & Changelog“). Dort sind pro Version die Änderungen (Bugfixes, Ergänzungen, Features) kurz beschrieben.

Für Releases kann zusätzlich eine Datei `CHANGELOG.md` im Root gepflegt werden (optional).

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
   - `frontend/package.json` → `version` (oder `npm run prebuild` aus dem Frontend-Ordner).
   - `frontend/src-tauri/tauri.conf.json` → `version`.

4. **Commit und Push**
   ```bash
   git add VERSION frontend/package.json frontend/src-tauri/tauri.conf.json frontend/src/pages/Documentation.tsx
   git commit -m "Doku & Version: Gabriels Änderungen (z. B. 1.0.1.5) ergänzt"
   git push origin main
   ```

So kannst du (Volker) Gabriels bereits gepushte Änderungen einholen und die Dokumentation sowie die Versionsnummernkontrolle dafür ergänzen und selbst committen/pushen.
