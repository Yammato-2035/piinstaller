# Lizenzierung — Setuphelfer

> ENTWURF, Stand 28.07.2026 — vor Veröffentlichung anwaltlich prüfen lassen.

## Aktueller Stand vor diesem Wechsel

Bis einschließlich Version 1.9.19.5 stand dieses Repository unter der
**MIT-Lizenz**, Copyright bei Gabriel Glienke & Contributors. Dieser Stand
bleibt für bereits erfolgte, extern nachweisbare Kopien/Forks gültig
(Bestandsschutz). Nach interner Prüfung gibt es keine bekannten externen
Klone oder Verteilungen vor diesem Wechsel — siehe Rechteübertragungs-
vereinbarung und Vorgeschichte im Projekt.

## Neuer Stand ab [Versionsnummer/Datum einfügen]

Ab diesem Zeitpunkt steht der Setuphelfer-Core unter:

**GNU Affero General Public License v3.0 (AGPLv3)**
mit einer zusätzlichen Erlaubnis (siehe `COMMERCIAL-EXCEPTION.md`), die es
ausschließlich dem jeweiligen Rechteinhaber erlaubt, proprietäre
Zusatzmodule (Cloud Edition Pro, App-Store-Module, Serverguide) zu
vertreiben, ohne dass die AGPLv3-Copyleft-Pflicht auf diese Zusatzmodule
durchschlägt.

**Warum AGPLv3 statt MIT:** MIT erlaubt jedem Dritten — auch
kommerziellen Hosting-Anbietern — den Code zu forken, umzubenennen und
unverändert kommerziell weiterzuvertreiben, ohne etwas zurückgeben zu
müssen. AGPLv3 schließt genau diese Lücke: Wer den Core (auch nur als
Netzwerkdienst) anbietet, muss seine Änderungen am Core offenlegen.

**Warum nicht Business Source License (BSL):** BSL ist in den USA
etablierter als in Deutschland, kommunikativ erklärungsbedürftiger und
für ein Projekt mit Community-Ambition (Forum, Beta-Tester, YouTube)
schwerer vermittelbar als das bekanntere AGPLv3-Modell (Nextcloud u. a.).

## Was das für verschiedene Nutzergruppen bedeutet

| Gruppe | Auswirkung |
|---|---|
| Privatnutzer (Download, lokale Nutzung) | Keine Änderung — AGPLv3 erlaubt private Nutzung uneingeschränkt. |
| Entwickler, die beitragen | Unterzeichnen die Mitwirkenden-Vereinbarung (CLA), siehe `docs/legal/CLA-*`. |
| Beta-Tester | Unterzeichnen dieselbe Vereinbarung (Feedback-Abschnitt), vor Zugang zur Beta. |
| Hosting-Anbieter / Dritte, die Setuphelfer als Dienst anbieten wollen | Müssen eigene Änderungen am Core offenlegen (AGPLv3 §13) — oder eine kommerzielle Lizenz beim Rechteinhaber erwerben. |
| Der Rechteinhaber selbst (Setuphelfer) | Darf proprietäre Zusatzmodule bauen, siehe `COMMERCIAL-EXCEPTION.md`. |

## Copyright-Header-Policy

Jede neue oder wesentlich geänderte Quelldatei im Core erhält am Dateianfang:

```
# Copyright (C) [Jahr] Volker Glienke (Setuphelfer)
# SPDX-License-Identifier: AGPL-3.0-only
# Zusätzliche Erlaubnis: siehe COMMERCIAL-EXCEPTION.md im Repository-Root.
```

Für Frontend-/TS-Dateien entsprechend mit `//`-Kommentaren. Bestehende
Dateien werden **nicht rückwirkend** in einem Big-Bang-Commit umgeschrieben
(das würde die Diff-Historie unnötig aufblähen) — stattdessen: Header wird
ergänzt, sobald eine Datei ohnehin bearbeitet wird ("touch it, header it").
Eine einmalige Stichtags-Ausnahme kann sinnvoll sein, wenn die Beta kurz
bevorsteht — das ist eine Entscheidung, die du triffst, keine technische.

## Offene Punkte vor tatsächlicher Veröffentlichung

- [ ] Anwaltliche Prüfung von LICENSE, COMMERCIAL-EXCEPTION.md, CLA und
      Rechteübertragungsvereinbarung
- [ ] Bestätigung: keine externen Kopien/Forks vor Stichtag (siehe oben)
- [ ] CLA-Unterschrift von Gabriel, Entwickler (Sri Lanka), Senior-Linux-Admin
      **vor** deren nächstem Commit nach Stichtag
- [ ] Rechteübertragung Gabriel → Volker unterschrieben
- [ ] Versionsnummer/Datum in diesem Dokument nachtragen
- [ ] `ckb-next`: prüfen, ob ein kompiliertes Binary auf den Rescue Stick
      gepackt wird (dann GPLv2-Pflichten des ckb-next-Projekts selbst
      gesondert beachten — unabhängig vom Setuphelfer-Lizenzwechsel)
