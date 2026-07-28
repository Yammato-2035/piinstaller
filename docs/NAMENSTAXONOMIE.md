# Namenstaxonomie „Companion" (Paket 5, E-10)

## Problem

Drei unterschiedliche Konzepte tragen aktuell "Companion" im Namen:

1. **Linux Companion / Remote Companion** (`docs/REMOTE_COMPANION.md`) —
   Smartphone-PWA, Pairing, Fernsteuerung von Modulen.
2. **Diagnose-Companion** (`docs/architecture/diagnose_companion.md`) —
   Interpreter für Events/Fehler, begrenzte UI.
3. **Panda-Companion** (`docs/panda-companion-roadmap.md`,
   `docs/user/GUIDED_UX_AND_COMPANION.md`) — Maskottchen/Guided-UX.

Für Beta-Tester ist "der Companion funktioniert nicht" damit strukturell
mehrdeutig — für Support und Bug-Reports ein direktes Reibungsrisiko.

## Vorschlag

| Bisher | Neuer Name (Nutzer-/UI-Text) | Neuer Name (intern, Code/Docs) | Begründung |
|---|---|---|---|
| Linux Companion / Remote Companion | **Linux Companion** (bleibt) | `remote_companion` / `RemoteCompanion*` (bleibt) | Das ist die einzige Funktion, die den Namen "Companion" im engeren Sinn verdient (ein zweites Gerät, das das erste begleitet). Bleibt Namensanker. |
| Diagnose-Companion | **Diagnose-Assistent** | `diagnosis_interpreter` / `DiagnosisInterpreter*` | Kein zweites Gerät, keine Fernsteuerung — reiner Interpreter. "Assistent" trifft die Funktion genauer und vermeidet Kollision. |
| Panda-Companion | **Panda-Guide** (oder „Setuphelfer-Panda") | `panda_guide` / `PandaGuide*` | Maskottchen/Guided-UX ist konzeptionell näher an "Guide" als an "Companion" — und trennt sich klar vom Remote-Feature. |

## Umsetzungsschritte (grob, Aufwand hängt vom Code-Anteil ab)

1. **Dokumentation zuerst umbenennen** — geringstes Risiko, sofort machbar:
   - `docs/architecture/diagnose_companion.md` → `docs/architecture/diagnose_assistent.md`
     (Inhalt anpassen: "Companion" → "Assistent" im Fließtext)
   - `docs/panda-companion-roadmap.md` → `docs/panda-guide-roadmap.md`
   - `docs/user/GUIDED_UX_AND_COMPANION.md` bleibt vom Namen her neutral,
     Fließtext auf "Panda-Guide" umstellen.
2. **UI-Texte** (i18n-Strings in `frontend/src/locales/de.json` etc.) —
   nach Begriff durchsuchen, wo "Companion" für Diagnose oder Panda im
   sichtbaren Text auftaucht, gegen "Assistent"/"Guide" austauschen.
   *Nicht* anfassen: alles, was sich auf den Linux/Remote Companion bezieht.
3. **Code-Bezeichner** (Klassen-/Modulnamen) — nur bei ohnehin anstehender
   Bearbeitung umbenennen ("touch it, rename it"), kein Big-Bang-Refactor
   nur wegen Naming — Rename-Risiko (Merge-Konflikte, IDE-Referenzen) ist
   höher als der Nutzen eines sofortigen Komplett-Umbaus.
4. **Support-/Community-Sprachgebrauch**: Sobald Schritt 1–2 gemacht sind,
   in Tutorials/Forum-Vorlagen konsistent nur noch "Linux Companion" für
   das Remote-Feature verwenden.

## Was ich NICHT vorschlage

Keine Umbenennung des Remote-Features selbst — "Linux Companion" ist
etabliert, in der Dokumentation verankert und trifft die Funktion am besten.
Die Verwirrung entsteht durch die anderen zwei, nicht durch dieses.
