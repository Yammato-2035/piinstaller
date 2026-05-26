# Dev Dashboard Roadmap FAQ

## Was ist die Roadmap-Registry?

Eine read-only Registry für Bereiche, Meilensteine, Aufgaben, Blocker, Entscheidungen, Evidence und den nächsten sinnvollen Cursor-Prompt.

## Warum ist das keine einfache To-do-Liste?

Weil eine To-do-Liste keine belastbare Aussage darüber trifft, was wirklich belegt ist, was nur teilweise grün ist und was aus Safety-Gründen blockiert oder zurückgestellt bleibt.

## Warum ist Restore zurückgestellt?

Weil kein geeignetes bootfähiges Rettungsmedium und kein nicht-produktives Zielsystem verfügbar sind. Ohne diese Voraussetzungen wäre ein echter Restore-End-to-End-Test nicht vertretbar.

## Warum ist Diagnostics nicht grün?

Weil echte Fehlerfälle, UI-Auswertung und eine belastbare Evidence-Matrix noch fehlen.

## Was muss künftig jeder Abschlussbericht enthalten?

Mindestens:

- Dashboard-Fortschritt
- Diagnostics-Lernfortschritt
- konkrete Evidence-Dateien
- die Next-Prompt-Entscheidung laut Registry
- ausdrücklich nicht ausgeführte Aktionen
- verbleibende `blocked`-/`deferred`-Bereiche

Ohne diese Punkte bleibt der Lauf fachlich unvollständig dokumentiert.

## Wie wird der nächste Prompt ausgewählt?

Der Algorithmus priorisiert fehlende Nachweise, wiederkehrende Dashboard-Unklarheiten, Safety-/Gate-Arbeit und vorhandene Architektur ohne ausreichende Evidence.

## Führt das Dashboard Runtime-Aktionen aus?

Nein. Die Registry ist Anzeige, Dokumentation und Prompt-Vorbereitung. Sie startet keine gefährlichen Aktionen.

## Was bedeuten `green`, `partial_green`, `blocked` und `deferred`?

- `green`: belastbar belegt
- `partial_green`: deutlicher Fortschritt, aber noch nicht vollständig freigegeben
- `blocked`: aktuell blockiert
- `deferred`: bewusst zurückgestellt

## Wie werden Evidence-Links genutzt?

Sie zeigen auf die Quellen, die einen Status fachlich tragen. Ohne belastbare Evidence gibt es kein künstliches Grün.

## Was passiert mit wiederholbaren Fehlern?

Sie werden künftig als Diagnosekandidaten behandelt: mit Fehlertext, Fehlercode, Ursache, Matcher, Empfehlung, Dashboard-Bereich, Evidence-Link und Testfall.

## Wofür sind Notizen gedacht?

Für sachliche Einordnung, offene Punkte und Entscheidungen. Nicht für versteckte Status-Manipulation.

## Was bringt der Prompt-Export?

Er erzeugt einen kopierbaren STRICT-MODE-Prompt mit Ziel, Grenzen, Sicherheitsregeln, Tests und Abschlussbericht.
