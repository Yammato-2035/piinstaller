# Dev Dashboard Roadmap-Registry

## Zweck

Die Roadmap-Registry im Setuphelfer Development Dashboard ist keine To-do-Liste und kein Execute-Modul. Sie ist ein read-only Steuerungs-, Dokumentations- und Prompt-Vorbereitungsmodul.

## Warum keine einfache To-do-Liste reicht

Eine reine To-do-Liste beantwortet nicht:

- was fachlich wirklich belegt ist
- welche Bereiche nur teilweise grün sind
- welche Blocker mehrere Folgearbeiten gleichzeitig sperren
- warum bestimmte Themen bewusst zurückgestellt wurden
- welcher nächste Cursor-Prompt fachlich sinnvoll ist

Die Registry kombiniert deshalb Bereiche, Meilensteine, Aufgaben, Blocker, Entscheidungen, Notizen, Evidence und Next Prompts.

## Statuswerte

- `green`: belastbar umgesetzt und belegt
- `partial_green`: substanzieller Fortschritt, aber noch nicht vollständig freigegeben
- `yellow`: in Arbeit oder nur teilweise belastbar
- `blocked`: fachlich oder technisch blockiert
- `deferred`: bewusst zurückgestellt
- `unknown`: nicht belegbar
- `deprecated`: nicht mehr aktiver Track

## Warum Restore zurückgestellt ist

Restore-End-to-End bleibt bewusst zurückgestellt, solange kein bootfähiges Rettungsmedium und kein nicht-produktives Zielsystem verfügbar sind. Das ist eine Safety-Entscheidung, keine Schönfärbung.

## Warum Diagnostics nicht vollständig grün ist

Diagnostics hat bereits Katalog-, API- und Strukturanteile. Vollständig grün wäre es aber erst mit echten Fehlerfall-Teststrecken, UI-Auswertung und einer belastbaren Evidence-Matrix.

## Verbindliche Abschlussregel für künftige Läufe

Jeder künftige Cursor-Lauf muss im Abschlussbericht sichtbar und mit Evidence beantworten:

1. welcher Dashboard-Bereich transparenter oder besser belegbar wurde
2. welche neue Diagnose / welcher neue Matcher / welcher neue Testfall gelernt wurde
3. welcher Next Prompt jetzt laut Registry gilt und warum
4. welche Evidence-Dateien den Fortschritt tragen
5. was ausdrücklich **nicht** ausgeführt wurde
6. was weiterhin `blocked`, `deferred` oder nur `partial_green` bleibt

Fehler dürfen nicht folgenlos bleiben: Wiederholbare Fehler sind künftig Diagnosekandidaten mit Fehlertext, Fehlercode, Ursache, Matcher, Empfehlung, Dashboard-Bereich, Evidence-Link und Testfall. `green` ist nur mit belastbaren Tests oder Runtime-/Hardware-Nachweisen zulässig; kein Fake-Green.

## Wie der Next Prompt berechnet wird

Die Auswahl priorisiert:

1. fehlende Nachweise, die mehrere Bereiche blockieren
2. wiederkehrende Unklarheiten im Dashboard
3. Safety-/Gate-Arbeit vor riskanter Runtime-Arbeit
4. vorhandene Architektur ohne ausreichende Evidence
5. keine Marketing-/Cloud-/HostPilot-Priorisierung vor Recovery-Core-Grün

## Warum das Dashboard keine Runtime-Aktionen ausführt

Die Roadmap-Registry zeigt nur an:

- Status
- Gründe
- Blocker
- Evidence
- den nächsten sinnvollen Prompt

Sie startet keine Backups, keine Restores, keine Rescue-Builds, kein Deploy und keinen Neustart.

## Evidence und Notizen

- Evidence-Links verweisen auf die belastbaren Quellen für einen Bereich.
- Notizen sind für sachliche Einordnung gedacht, nicht für verdeckte Status-Manipulation.

## Prompt-Export

Der Prompt-Export erzeugt einen STRICT-MODE-Text mit:

- Ziel
- Nicht-Zielen
- Sicherheitsregeln
- Phase-0-Gate
- konkreten Aufgaben
- erlaubten Bereichen
- verbotenen Aktionen
- Tests
- Doku-/FAQ-/i18n-Zielen
- Abschlussbericht
