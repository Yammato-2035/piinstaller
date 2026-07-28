# Setuphelfer Commercial Exception zur GNU AGPLv3

> ENTWURF — vor Veröffentlichung anwaltlich prüfen lassen.

Diese Zusatzvereinbarung ergänzt die GNU Affero General Public License,
Version 3 ("AGPLv3"), unter der der Setuphelfer-Core (dieses Repository)
lizenziert ist. Sie ist eine zusätzliche Erlaubnis im Sinne von
AGPLv3 Abschnitt 7 ("Additional Permissions").

## 1. Zweck

Die AGPLv3 verpflichtet jeden, der eine modifizierte Version dieser Software
über ein Netzwerk anbietet, den vollständigen Quellcode der modifizierten
Version offenzulegen. Diese Ausnahmeregelung stellt klar, unter welchen
Bedingungen der Rechteinhaber selbst proprietäre Zusatzmodule (z. B.
Setuphelfer Cloud Edition Pro, Setuphelfer App-Store-Module, Setuphelfer
Serverguide) entwickeln und vertreiben darf, ohne dass diese Zusatzmodule
selbst unter die AGPLv3 fallen — sofern sie über eine dokumentierte,
stabile Schnittstelle (API/Plugin-Grenze, siehe `public-contracts`) an den
Core andocken und keine Modifikation des Core-Quellcodes selbst darstellen.

## 2. Wer die Ausnahme nutzen darf

Diese Ausnahmeregelung gilt **ausschließlich** zugunsten des Rechteinhabers
des Setuphelfer-Projekts (aktuell: Volker Glienke; nach Gründung
automatisch die dann zuständige Gesellschaft). Sie ist **nicht** auf
Dritte übertragbar. Ein Dritter, der den Core forkt und eigene
Zusatzmodule baut, unterliegt weiterhin uneingeschränkt der AGPLv3 —
inklusive der Pflicht, Modifikationen am Core selbst offenzulegen, wenn
er sie über ein Netzwerk anbietet.

## 3. Was NICHT unter die Ausnahme fällt

- Modifikationen am Core-Quellcode selbst (`backend/app.py`,
  `deploy/routes.py` und alle weiteren Core-Module) — diese bleiben
  vollständig AGPLv3-pflichtig, auch beim Rechteinhaber selbst, sofern
  sie öffentlich als Teil des Core-Repositories geführt werden.
- Jede Nutzung durch Dritte, die nicht der aktuelle bzw. künftige
  Rechteinhaber sind.

## 4. Verhältnis zum public-contracts-Submodul

Die in `public-contracts` dokumentierte Schnittstellengrenze zwischen
öffentlichem Core und privaten Zusatzmodulen ist die technische
Grundlage, auf der sich diese Ausnahme stützt. Änderungen an dieser
Grenze (z. B. wenn ein "Zusatzmodul" tatsächlich Core-Interna direkt
einbindet statt über die dokumentierte API) können dazu führen, dass ein
Modul entgegen der Absicht doch als AGPLv3-pflichtige Modifikation
gilt. Diese Grenze sollte bei jeder größeren Architekturänderung erneut
geprüft werden (siehe auch ADR zu SP- vs. TEL-Telemetrie, Paket 4).

---

*Diese Datei ist Teil des Lizenzpakets von Setuphelfer und ergänzt die
Datei `LICENSE` im Repository-Root. Im Konfliktfall hat der Wortlaut der
AGPLv3 selbst Vorrang; diese Datei dient der Klarstellung der
zusätzlichen Erlaubnis nach AGPLv3 §7.*
