# ADR-0001: SP-002 (privater Microservice) vs. TEL-Series (Core-Router) — Telemetrie-Architektur

**Status:** Vorschlag — Entscheidung offen
**Datum:** 28.07.2026
**Entscheider:** Volker Glienke

## Kontext

Im Projekt existieren zwei parallele Implementierungen für Rescue-Stick-Telemetrie,
ohne dass bisher eine Architekturentscheidung dokumentiert wurde:

| | **TEL-Series (Core-Router)** | **SP-002 (privater Microservice)** |
|---|---|---|
| Ort | `backend/rescue_telemetry/routers.py` (80 Zeilen) + `backend/core/rescue_telemetry_ingest.py` (453 Zeilen) + `backend/core/rescue_telemetry_tasks.py` (163 Zeilen) — **eingebettet im Core-Monolithen** | `docs/private-server-skeletons/telemetry-server/app/main.py` (70 Zeilen) — **eigenständiger FastAPI-Service, Port 8101** |
| Mount-Punkt | `/api/rescue/telemetry/*` innerhalb der Haupt-App | Eigener Prozess, eigener Port, referenziert `public-contracts`-Schema direkt |
| Umfang | Ingest, Task-Pull (`tasks/next`, `tasks/result`, `tasks/status`) — **mehr Funktionsumfang** | Nur Ingest + Dry-Run, dafür mit **Forbidden-Route-Schutz und Privacy-Gate von Anfang an eingebaut** |
| Reifegrad | Deutlich mehr Code, in Produktion eingebunden | Skelett, für Lab/Beta gedacht |

### Kritischer Befund: inkompatible Protokollversionen

Das ist keine reine Stilfrage. Die beiden Implementierungen akzeptieren
**unterschiedliche, sich gegenseitig ausschließende Schemas:**

- `backend/core/rescue_telemetry_ingest.py:255`
  ```python
  if schema_version not in (1, "1", "1.0", "1.0.0"):
      return False, TELEMETRY_ERROR_CODES["schema_invalid"]
  ```
  Akzeptiert nur `payload_kind` `rescue_boot_network_telemetry` (Schema v1.x)
  oder `windows_rescue_inspect`.

- `docs/private-server-skeletons/telemetry-server/app/main.py:33`
  ```python
  if payload.get("schema_version") != "telemetry.rescue.beta.v2":
      return JSONResponse(status_code=422, content={"accepted": False, "status": "rejected_schema"})
  ```
  Akzeptiert ausschließlich `"telemetry.rescue.beta.v2"`.

**Konsequenz:** Ein Rescue Stick, der im v2-Beta-Format sendet (das Format,
auf das sich `public-contracts` und die private Serie beziehen), würde vom
Core-Endpunkt mit `TELEMETRY-SCHEMA-001` abgelehnt. Umgekehrt würde der
private Microservice ein v1.0.0-Boot-Network-Payload mit `rejected_schema`
zurückweisen. **Falls beide Endpunkte parallel erreichbar sind (z. B. Core
lokal auf dem Stick, SP-002 in der Cloud über `telemetrie.setuphelfer.de`),
hängt es aktuell vom Zufall der Konfiguration ab, welcher Stick-Build gegen
welchen Endpunkt überhaupt funktioniert.**

## Optionen

### Option A: TEL-Series wird kanonisch, SP-002-Skelett wird verworfen
- **Vorteil:** Mehr Funktionsumfang bereits vorhanden (Task-Pull-Mechanismus
  fehlt in SP-002 komplett). Kein zweiter Prozess/Port zu betreiben.
- **Nachteil:** Widerspricht der in `PUBLIC_PRIVATE_BOUNDARY_V1.md`
  dokumentierten Architekturentscheidung (öffentlich = Contracts/Mocks,
  privat = Produktionsserver). Der Core würde dauerhaft produktionsrelevante
  Telemetrie-Logik im öffentlichen Repository tragen — das ist eine
  Rückabwicklung einer bereits getroffenen, dokumentierten Entscheidung.
  Verschärft zusätzlich die Monolith-Größe (`app.py`/Core-Module), die
  ohnehin schon in Dekomposition ist.
- **Migrationsaufwand:** Gering kurzfristig (nichts zu bauen), aber hohe
  versteckte Kosten: private Serie (SP-001/003/004) ist auf die
  Trennung öffentlich/privat ausgelegt; TEL dauerhaft im Core zu belassen
  bedeutet, diese Trennung für den wichtigsten Datenfluss aufzugeben.

### Option B: SP-002 wird kanonisch, TEL-Series-Router wird migriert/entfernt
- **Vorteil:** Konsistent mit der bereits getroffenen Public/Private-
  Grenzentscheidung. Schema-Referenz direkt aus `public-contracts` — ein
  Schema, eine Quelle der Wahrheit. Reduziert Core-Monolith-Umfang um
  ~700 Zeilen (passt zur laufenden Dekomposition, Phasen B.3–B.5).
- **Nachteil:** Task-Pull-Mechanismus (`tasks/next`, `tasks/result`,
  `tasks/status`) existiert in SP-002 noch nicht — muss migriert/nachgebaut
  werden. Der Core braucht während der Übergangszeit einen Weg, Telemetrie
  weiterzuleiten oder der Stick muss umkonfiguriert werden, gegen den neuen
  Endpunkt zu senden.
- **Migrationsaufwand:** Mittel. Grobschätzung: 2–4 Arbeitstage für
  Task-Pull-Portierung nach SP-002, plus Stick-seitige Konfigurationsanpassung
  (Ziel-URL, Schema-Version), plus Regressionstests gegen die 1.624
  bestehenden Tests, soweit sie TEL-Routen berühren.

### Option C: Hybrid mit Migrationsfenster (empfohlene Reihenfolge, keine Dauerlösung)
- TEL-Series bleibt für eine definierte Übergangszeit (Vorschlag: bis
  Hardware-Testkette auf allen Zielgeräten abgeschlossen ist) als
  **Compatibility-Layer** bestehen, akzeptiert aber zusätzlich Schema v2
  (Erweiterung von `validate_envelope`, nicht Ersatz).
- SP-002 wird parallel um Task-Pull ergänzt und zur echten Zielarchitektur.
- Nach Abschluss der Übergangszeit: TEL-Router aus dem Core entfernen
  (Aufräumschritt, konkret terminiert statt "irgendwann").
- **Vorteil:** Kein Big-Bang-Schnitt während der Hardware-Testphase, die
  gerade läuft. Vermeidet, zwei kritische Migrationen gleichzeitig zu
  fahren (Hardware-Stabilisierung + Protokollumzug).
- **Nachteil:** Für die Übergangszeit existieren de facto weiterhin zwei
  Schemas — nur bewusst befristet statt unbewusst dauerhaft, wie aktuell.
- **Migrationsaufwand:** Ähnlich Option B, zusätzlich ein Enddatum im
  Kalender/Reminders, das auch tatsächlich eingehalten werden muss (sonst
  wird aus dem befristeten Zustand der aktuelle Dauerzustand nur mit
  neuem Datum).

## Entscheidungskriterien

- Übereinstimmung mit bereits getroffener Public/Private-Grenzentscheidung
  (`PUBLIC_PRIVATE_BOUNDARY_V1.md`) — spricht strukturell für B oder C.
- Laufende Monolith-Dekomposition (Phasen B.3–B.5) — spricht gegen A.
- Aktuelle Priorität: Hardware-Testkette auf MSI/Pi5/Pi3b/Laptop — spricht
  für C, um nicht zwei Migrationen gleichzeitig zu fahren.
- Wie kritisch ist Datenverlust während der Übergangszeit? Wenn ein Stick
  im Feld (Beta-Tester) telemetrie sendet und abgelehnt wird, entsteht ein
  stiller Datenverlust ohne Fehlermeldung beim Nutzer (Telemetrie läuft
  im Hintergrund) — das spricht dafür, das Schema-Problem VOR der
  kontrollierten Beta zu lösen, unabhängig davon welche Option gewählt wird.

## Entscheidung

*[Vom Entscheider auszufüllen]*

☐ Option A ☐ Option B ☐ Option C ☐ Andere: _______________

## Konsequenzen

*[Nach Entscheidung auszufüllen — u.a. welches Team-Mitglied die Migration
übernimmt, Zieldatum, welche Tests zusätzlich geschrieben werden müssen um
die Schema-Kompatibilität selbst automatisiert zu prüfen (Empfehlung:
unabhängig von der gewählten Option einen Test schreiben, der beide
Schema-Versionen gegen den gewählten kanonischen Endpunkt sendet und das
erwartete Verhalten — Annahme oder definierter Fehler statt stillem
Datenverlust — verifiziert).]*

## Referenzen

- `backend/rescue_telemetry/routers.py`
- `backend/core/rescue_telemetry_ingest.py` (Zeile 255: Schema-v1-Check)
- `backend/core/rescue_telemetry_tasks.py`
- `docs/private-server-skeletons/telemetry-server/app/main.py` (Zeile 33: Schema-v2-Check)
- `docs/private-server-skeletons/README.md`
- `docs/architecture/PUBLIC_PRIVATE_BOUNDARY_V1.md`
- Projekt-Memory: "Most significant structural risk: Two parallel telemetry
  architectures (SP vs. TEL series) coexist without an explicit
  architectural decision"

## Nachtrag zu E-13 (public-contracts-Submodul)

Ursprünglich als offener Punkt geführt ("public-contracts fehlt in
`.gitmodules`"). Nach Prüfung von `docs/private-server-skeletons/README.md`
und `docs/architecture/PUBLIC_PRIVATE_BOUNDARY_V1.md`: **kein Fehler.**
`public-contracts` ist als Submodul-Rückverweis von der *privaten* Serie
auf *dieses* öffentliche Repository konzipiert — das Submodul gehört ins
`.gitmodules` der privaten Repos, nicht hierher. E-13 wird als erledigt/
gegenstandslos aus der offenen Liste genommen.
