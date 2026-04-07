# Backup & Restore – Phase 3 Freigabebewertung (Go / No-Go)

Stand: konsolidiert aus Phase 0–2E (kein neuer Laufzeitnachweis in Phase 3).

## Gesamturteil (harte Linie)

- **Vollständiges GO** für die **Kernfunktion Backup inkl. Laufzeit**: **nicht** belegbar (kein echter Backup-Lauf in der Referenzumgebung verifiziert).
- **Gesamtmodul (funktionale Freigabe): NO-GO** – siehe Matrix und Begründung unten.
- Teilbereiche (UI, Vertrag, einzelne API-Pf ohne Backup-Job) können **Bedingt Go** sein; das ersetzt **kein** Gesamt-GO.

## Go-/No-Go-Matrix (Kurzfassung)

| Bereich | Status | Beleg | Nächster Schritt |
|---------|--------|-------|------------------|
| BackupRestore-Seite (Build, Struktur) | Bedingt Go | Build/Statik | Nutzertests auf Zielsystem |
| i18n Modul | Bedingt Go | Phasen 1/2B, Key-Parität 2D | Inhaltliche QA |
| API-Vertrag code/severity/details | Bedingt Go | 2A–2C, statisch + Teil-HTTP | Backup-Lauf gegen Vertrag prüfen |
| Verify (HTTP-Teilpfade) | Bedingt Go | 2D real | API-erzeugtes Archiv |
| List / Delete (HTTP-Teilpfade) | Bedingt Go | 2D real | Last/Fehler auf Pi |
| Restore Preview / Dry-Run | Bedingt Go | 2D real | Größere Archive |
| Root-/Produktiv-Restore | No-Go / absichtlich gesperrt | Code + Gate | Bewusste Policy |
| Echter Backup-Lauf | **Ungeprüft / Blocker** | 2E: Sudo + keine Mini-Semantik | Zielsystem + Testkonzept |
| Job-Lifecycle / Konflikt / Cancel | **Ungeprüft / Blocker** | nur Code | Zwei Jobs mit Sudo |
| Cloud / USB / Clone live | **Ungeprüft** | — | Hardware/Anbieter |
| Sicherheit Allowlist / Root-Block | Bedingt Go | Code + Teil-HTTP | Penetration light auf Pi |
| **Gesamtmodul funktional** | **NO-GO** | oben | Freigabeblocker abarbeiten |

## Freigabeblocker (hart)

1. Kein **real verifizierter** erfolgreicher **Backup-Lauf** über die API (Referenzumgebung).
2. **Job-Pfade** (Status, Konflikt, Cancel) **praktisch unbelegt**.
3. Kein **risikoarmer** reiner Testdaten-Backup-Modus in der API → erschwert wiederholbare Verifikation ohne System-tar.

## Nächste Maßnahmen (priorisiert)

1. **Freigabeblocker:** Backup auf **Zielsystem** (oder Staging mit Sudo) mit dokumentiertem Szenario; anschließend List + Verify auf erzeugter Datei.
2. **Freigabeblocker:** Gleiche Umgebung: **async Job** durchspielen, optional zweiter Start → `job_conflict`.
3. **Wichtig:** Cloud/USB/Clone je nach Produktumfang **gezielt** auf Hardware/Account.
4. **Später:** Legacy-Fallbacks im Frontend reduzieren, wenn Backend überall `code` liefert.

## Was nicht behauptet wird

- Produktionsreife, vollständige funktionale Freigabe, verifizierte Parallelität, Live-Cloud/USB/Clone.

---

## Phase 4 (UI): Ampel-Anzeige – Umsetzungshinweis

Die Ampel auf `BackupRestore` ist **nicht** als „Backup OK“, sondern als **Freigabelage / Restrisiko** zu lesen:

- **Gelb (Standard):** solange kein nachgewiesener erfolgreicher Backup-Lauf + Verify auf diesem Archiv als persistierter Fakt vorliegt (aktuell: `hasRealBackupVerification = false` im Frontend).
- **Rot:** wenn `backup.sudo_required` beim Create-Versuch erkannt wurde **oder** klassische Risiko-Signale (Diagnose kritisch / Restore-Vorschau aktiv) greifen.
- **Grün:** in der aktuellen Freigabelage **nicht** erreichbar (bewusst), bis die o. g. Nachweise existieren.

Texte: i18n unter `backup.ui.traffic.*` und `backup.ui.trafficReason.*` (keine Hardcodes in der Badge-Zeile).
