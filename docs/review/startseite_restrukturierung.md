# Startseite – Restrukturierungsvorschlag (Audit-basiert)

Datum: 2026-03-20  
Ziel: bessere Nutzerführung, weniger Redundanz, klarer Release-Stand

## A) Kritische Bewertung des aktuellen Zustands

## Nutzerführung
- Positiv: Hauptnutzen und Kernpfade sind erkennbar.
- Problem: Zu viele Sektionen in Folge erzeugen Entscheidungslast statt Klarheit.

## Visuelle Hierarchie
- Positiv: Hero und Kartenstil sind konsistent.
- Problem: Mehrere Teaserblöcke konkurrieren auf derselben Prioritätsstufe.

## Hero-Wirkung
- Positiv: Linux/Raspberry-Pi/App-Bezug ist vorhanden.
- Problem: sichtbarer `Asset-Slot` wirkt wie nicht finalisiertes UI.

## CTA-Klarheit
- Positiv: Primär-/Sekundär-CTA vorhanden.
- Problem: CTA-Signale verteilen sich über zu viele Sektionen.

## Screenshot-Nutzung
- Positiv: echte Screenshots eingebunden.
- Problem: Pfadstrategie (`/docs/...`) ist deployment-abhängig und fehleranfällig.

## White-Space und Kartenlogik
- Positiv: Layout nutzt Luft und konsistente Karten.
- Problem: inhaltliche Wiederholung reduziert wahrgenommene Qualität.

## Mobile-Lesbarkeit
- Positiv: Grids brechen responsiv auf.
- Problem: Seitenlänge und Wiederholung sind mobil zu hoch.

---

## B) Neue empfohlene Reihenfolge (Release-fähig)

1. **Hero (final, ohne sichtbaren Asset-Slot)**
2. **Problem/Nutzen (3 Kernpunkte)**
3. **Live-Status + Build-Screenshots (Produktbeweis gebündelt)**
4. **Funktionsübersicht (Installation, Diagnose, Backup, Konfiguration, Projekte)**
5. **Lernpfade (Anfänger/Fortgeschritten/Experte)**
6. **Projekte + Tutorials als kombinierter Praxisblock**
7. **Community + Download als Abschluss-CTA**

---

## C) Elemente, die verschoben/zusammengelegt/entfernt werden sollten

## Entfernen
- Sichtbare Hero-Komponente `asset-slot` (nur intern als Entwicklungs-Slot behalten).

## Zusammenlegen
- „Visuelle Teaser-Bausteine“ in „Funktionsübersicht“ integrieren.
- „Tutorials mit Projektbezug“ + „Community/Forum“ + „Download-Hinweis“ zu einem Abschluss-CTA-Block bündeln.

## Verschieben
- Build-Screenshots näher an Live-Status platzieren (glaubwürdiger Produktnachweis).

---

## D) Konkrete Strukturblöcke mit Pflicht-CTA

| Block | Pflichtinhalt | Pflichtaktion |
|---|---|---|
| Hero | Nutzen + Product Scene + 2 CTAs | `Download`, `Geführter Einstieg` |
| Nutzen | 3 Problemlösungen | Link zu `Tutorials` |
| Produktbeweis | Live-Daten + echte Screenshots | Link zu `Download`/`Doku` |
| Funktionen | Kernmodule | Link zu jeweiliger Unterseite |
| Lernpfade | 3 Niveaus | Link zu passenden Tutorials |
| Praxisblock | Projekte + Tutorials | Link zu `Projekte` und `Tutorials` |
| Abschluss | Community + Download | Link zu `Community`, `Download`, `Fehlerhilfe` |

---

## E) Abnahmekriterien für die Startseite

- Keine sichtbaren Asset-Slots/Platzhalterlabels im Live-UI.
- Keine CTA-Dopplung über mehrere gleichwertige Blöcke.
- Maximal 7 Hauptsektionen nach Hero.
- Jede Sektion hat: Überschrift, Kurztext, visuelle Stütze, klare Weiteraktion.
- Produktbeweis (Screenshots + Live-Status) in einer nachvollziehbaren Einheit.
